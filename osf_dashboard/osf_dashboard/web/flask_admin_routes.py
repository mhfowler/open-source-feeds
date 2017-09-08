"""
configuration for flask-admin, for Julian to access the database
see documentation of flask-admin here: https://flask-admin.readthedocs.io/en/latest/
"""
from flask import Response
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib import sqla

from osf_dashboard.settings import FLASK_ADMIN_URL
from osf_dashboard.models import TestObject, User
from osf_dashboard.web.extensions import db, basic_auth


def get_flask_admin():
    """
    initializes flask-admin with all of the correct models,
    should be called during create_app in app.py

    To logout of Basic-Auth: visit chrome://restart
    """
    def redirect_to_basic_auth_login():
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    # '/admin/ page
    class HomeView(AdminIndexView):
        def is_accessible(self):
            if not basic_auth.authenticate():
                return False
            else:
                return True
        def inaccessible_callback(self, name, **kwargs):
            return redirect_to_basic_auth_login()

        @expose('/')
        def index(self):
            return self.render('admin_index.html')
    admin = Admin(
        index_view=HomeView(url=FLASK_ADMIN_URL),
        url=FLASK_ADMIN_URL,
        name='Continuum',
        template_mode='bootstrap3'
    )

    # base admin model
    class HelloModelView(sqla.ModelView):
        column_display_pk = True
        column_hide_backrefs = False

        def is_accessible(self):
            if not basic_auth.authenticate():
                return False
            else:
                return True

        def inaccessible_callback(self, name, **kwargs):
            return redirect_to_basic_auth_login()

    # Add administrative views here
    admin.add_view(HelloModelView(TestObject, db.session))
    admin.add_view(HelloModelView(User, db.session))

    # return admin
    return admin