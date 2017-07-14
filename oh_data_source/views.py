import logging
import os

import arrow
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import UploadFileForm
from .models import OpenHumansMember, RawTakeoutData
from .tasks import xfer_to_open_humans

# Open Humans settings
OH_BASE_URL = 'https://www.openhumans.org'

APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://127.0.0.1:5000')
APP_PROJ_PAGE = 'https://www.openhumans.org/activity/seeq/'

# Set up logging.
logger = logging.getLogger(__name__)


def oh_get_member_data(token):
    """
    Exchange OAuth2 token for member data.
    """
    req = requests.get(
        '{}/api/direct-sharing/project/exchange-member/'.format(OH_BASE_URL),
        params={'access_token': token})
    if req.status_code == 200:
        return req.json()
    raise Exception('Status code {}'.format(req.status_code))
    return None


def oh_code_to_member(code):
    """
    Exchange code for token, use this to create and return OpenHumansMember.

    If a matching OpenHumansMember already exists in db, update and return it.
    """
    if settings.OH_CLIENT_SECRET and settings.OH_CLIENT_ID and code:
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': '{}/complete'.format(APP_BASE_URL),
            'code': code,
        }
        req = requests.post(
            '{}/oauth2/token/'.format(OH_BASE_URL),
            data=data,
            auth=requests.auth.HTTPBasicAuth(
                settings.OH_CLIENT_ID,
                settings.OH_CLIENT_SECRET
            ))
        data = req.json()
        if 'access_token' in data:
            oh_id = oh_get_member_data(
                data['access_token'])['project_member_id']
            try:
                oh_member = OpenHumansMember.objects.get(oh_id=oh_id)
                logger.debug('Member {} re-authorized.'.format(oh_id))
                oh_member.access_token = data['access_token']
                oh_member.refresh_token = data['refresh_token']
                oh_member.token_expires = OpenHumansMember.get_expiration(
                    data['expires_in'])
            except OpenHumansMember.DoesNotExist:
                oh_member = OpenHumansMember.create(
                    oh_id=oh_id,
                    access_token=data['access_token'],
                    refresh_token=data['refresh_token'],
                    expires_in=data['expires_in'])
                logger.debug('Member {} created.'.format(oh_id))
            oh_member.save()

            return oh_member
        elif 'error' in req.json():
            logger.debug('Error in token exchange: {}'.format(req.json()))
        else:
            logger.warning('Neither token nor error info in OH response!')
    else:
        logger.error('OH_CLIENT_SECRET or code are unavailable')
    return None


def index(request):
    """
    Main page for app: invites login, or displays upload form and data.
    """
    oh_member = None
    oh_data = None
    form = None

    if request.user.is_authenticated:
        oh_member = request.user.openhumansmember
        try:
            oh_data = oh_get_member_data(oh_member.get_access_token())
        except:
            logout(request)
            return redirect('/')

        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                logger.debug('Valid form!!!')
                try:
                    uploaded = RawTakeoutData.objects.get(user=request.user)
                    uploaded.delete()
                except RawTakeoutData.DoesNotExist:
                    pass
                print(request.POST)
                uploaded = RawTakeoutData(datafile=request.FILES['file'],
                                          user=request.user)
                uploaded.save()
                oh_member.last_xfer_datetime = arrow.get().format()
                oh_member.last_xfer_status = 'Queued'
                oh_member.save()
                xfer_to_open_humans(
                    oh_id=oh_member.oh_id, file_id=uploaded.id,
                    granularity=request.POST['granularity'],
                    search_string=request.POST['search_string'])
                messages.success(request, 'Data processing initiated')
            else:
                logger.debug('INVALID FORM')
        else:
            form = UploadFileForm()

    context = {'client_id': settings.OH_CLIENT_ID,
               'oh_proj_page': settings.OH_ACTIVITY_PAGE,
               'form': form,
               'oh_member': oh_member,
               'oh_data': oh_data,
               }
    return render(request, 'oh_data_source/index.html', context=context)


def complete(request):
    """
    Receive user from Open Humans. Store data, start data upload task.
    """
    logger.debug("Received user returning from Open Humans.")

    # Exchange code for token.
    # This creates an OpenHumansMember and associated User account.
    code = request.GET.get('code', '')
    oh_member = oh_code_to_member(code=code)

    if oh_member:

        # Log in the user.
        user = oh_member.user
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Return user to index, which should now display a form.
        return redirect('/')

    logger.debug('Invalid code exchange. User returned to starting page.')
    return redirect('/')


def deletedata(request):
    if request.user.is_authenticated:
        try:
            data = RawTakeoutData.objects.get(user=request.user)
            data.delete()
            messages.info(request, 'Data deleted.')
        except RawTakeoutData.DoesNotExist:
            pass
    else:
        messages.error(request, 'Error re: Data deletion. User not logged in.')
    return redirect('/')
