# Google Search History

## About

This is a Django/Celery app used to process Google Takeout data to extract
search data, process it, and add the results to Open Humans as a data source.

## Local development instructions

### Local requirements.

1. Foreman https://github.com/ddollar/foreman (This package may be installed with a simple `gem install foreman`)
2. RabbitMQ https://www.rabbitmq.com/download.html
3. pip https://pip.pypa.io/en/stable/installing/

### Install Python requirements.

**It is Strongly recommend you use [virtualenv](https://virtualenv.pypa.io/en/stable/).**
**Be advised you need to use a name other than the default `.env` for the python environment; we suggest `.env_$YOURPROJECT`**

To create your 'virtualenv' run:

  `virtualenv -v --python=python3 .env_$YOURPROJECT`

To activate your 'virtualenv' you need to run:

  `source .env_$YOURPROJECT/bin/activate`

Next install all of the required python dependancies with:

  `pip install -r requirements_p3.txt`

---

### Set up `.env` for `foreman`

Copy `env.example` to `.env`.

This file contains secrets and other configurations for running the app.
When you use foreman to run this app, it will load `.env` to be environment
variables.
**Keep your version SECRET! Never commit it to git.**

### Install `RabbitMQ` for your system

Documentation for supported systems includes [Linux (apt&rpm), OS X/macOS, and Other Unixes (including BSDs), as well as Windows](https://www.rabbitmq.com/platforms.html)

### Make sure that `RabbitMQ` is started

This is distribution dependent, both in syntax and name.
- With the very popular Ubuntu and other Debian based systems, it will likely be started for you after you install the package, but can also start it manually with: `sudo rabbitmq-server start`
- With Homebrew on OS X/macOS run `brew services rabbitmq start`
- [RabbitMQ](https://www.rabbitmq.com/) has it's control system similar to `apachectl`, The documentation is online if you would like to learn more about [rabbitmqctl](https://www.rabbitmq.com/man/rabbitmqctl.1.man.html)
If you have other questions please refer to your [distribution reference page at `RabbitMQ`](https://www.rabbitmq.com/platforms.html)

### Create Open Humans project

You need to create an OAuth2 project in Open Humans. Start here:
https://www.openhumans.org/direct-sharing/projects/manage/

This is what members join and authorize. Some recommended settings:
1. **Fill out the "Description of data you plan to upload".** This identifies
  your project as a data source. If it's left blank, Open Humans assumes
  your project doesn't plan to add data.
2. **Set the enrollment URL to http://127.0.0.1:5000**
  **The default development setup automatically sets the Redirect URL to http://127.0.0.1:5000/complete**

---

Once the project is created, click on the project's name in your [project
management page](https://www.openhumans.org/direct-sharing/projects/manage/).
This will show the project's information.

Get the `Activity page`, `Client ID` and `Client secret` and set these in
your `.env`. The ID and secret identify and authorizes your app. You'll use
these to get user authorization and manage user data.

**Keep your Client secret private.** Secret data should not be committed to a
repository. In Heroku, this data is set as environment variables. Locally,
you can use a custom `.env`.

### Initialize the database and static assets.

Note: Django will use SQLite3 for local development unless you set
`DATABASE_URL` in your `.env`.

In the project directory, run the `migrate` command with foreman:
`foreman run python manage.py migrate`

In the project directory, run the `collectstatic` command with foreman:
`foreman run python manage.py collectstatic`
**You will receive a warning message similar to:**
```
You have requested to collect static files at the destination
location as specified in your settings:

    development:~/your_project/staticfiles

This will overwrite existing files!
Are you sure you want to do this?
```

This is normal! You **WILL** want to overwrite the files, theres is likely no folder even created yet, so nothing stored there currently in any case.

---

### Run.

You can now start `foreman` in the foreground with: `foreman start`
   Note you will receive the warning: `warnings.warn('Using settings.DEBUG leads to a memory leak, never '`. This is normal, and sadly part of the debugging process of Django.

If you're curious as to the root cause of this [StackOverflow has a full writeup](http://stackoverflow.com/questions/4806314/disable-django-debugging-for-celery)

Now point your browser to (http://127.0.0.1:5000/) you should be greated with a fairly generic openhumans page, with some of your `project` information that you added in the `foreman` .env file.

---

## Heroku deployment notes

Heroku has a lot of features and documentation. The notes below can
help you get started &ndash; you should feel free to explore more!

### Prerequisites and local requirements

1. Create a Heroku account
2. Install the Heroku Commant Line Interface (formally "Heroku Toolbelt"):
https://devcenter.heroku.com/articles/heroku-cli

### Log in and create your app

It's common for the app to have the same name as the project slug. The name
matters if you plan to use Heroku's default domain, which is free (e.g. `https://your-app-name.herokuapp.com`).

1. `heroku login`
2. `heroku apps:create your-app-name`

### Configure and add add-ons

Find your app in the Heroku Dashboard:  https://dashboard.heroku.com/apps

Go to **"Resources tab"** and add:
1. **CloudAMQP** (Little Lemur: Free)
2. **Heroku Postgres** (Hobby Dev: Free)

Go to **"Settings tab"** and add environment variables (as with `.env`):
1. **OH_CLIENT_ID**
2. **OH_CLIENT_SECRET**
3. **OH_ACTIVITY_PAGE**
4. **APP_BASE_URL** (e.g. `https://your-app-name.herokuapp.com` &ndash; no trailing dash!)
5. **SECRET_KEY**
7. **DEBUG** = true when needed

### Push your code.

Run this to initialize and update your code in Heroku:
`git push heroku master`

### Watch logs.

`heroku logs -t`
