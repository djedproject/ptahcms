""" app management module """
import ptah, ptahcms
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IRequest, IRouteRequest

from ptah.manage import manage
from ptahcms import form

MANAGE_APP_ROUTE = MANAGE_APP_CATEGORY = 'ptah-manage-app'


@manage.module('apps')
class ApplicationsModule(manage.PtahModule):
    __doc__ = 'A listing of all registered Ptah Applications.'

    title = 'Applications'

    def __getitem__(self, key):
        for id, factory in ptahcms.get_app_factories().items():
            if factory.name == key:
                app = factory()
                app.__parent__ = self
                app.__root_path__ = '/ptah-manage/apps/%s/'%app.__name__
                return app

        raise KeyError(key)

    def available(self):
        return bool(ptahcms.get_app_factories())


@view_config(
    context=ApplicationsModule,
    renderer=ptah.layout('ptahcms-manage:apps.lt', 'ptah-manage'))

class ApplicationsModuleView(ptah.View):
    """ Applications module default view """

    def update(self):
        factories = []
        for factory in ptahcms.get_app_factories().values():
            factories.append((factory.title, factory))

        self.factories = [f for _t, f in sorted(factories)]


@view_config(
    context=ptahcms.IApplicationRoot,
    renderer=ptah.layout('ptahcms-manage:apps-contentview.lt', 'ptah-manage'))

class ViewForm(form.Form):

    readonly = True

    @property
    def fields(self):
        return self.context.__type__.fieldset

    def form_content(self):
        data = {}
        for name, field in self.context.__type__.fieldset.items():
            data[name] = getattr(self.context, name, field.default)

        return data


@view_config(
    name='sharing.html',
    context=ptahcms.IContent,
    renderer=ptah.layout('ptahcms-manage:apps-sharing.lt', 'ptah-manage'))

class SharingForm(form.Form):
    """ Sharing form """

    csrf = True
    fields = form.Fieldset(
        form.FieldFactory(
            'text',
            'term',
            title = 'Search term',
            description = 'Searches users by login and email',
            missing = '',
            default = '')
        )


    users = None
    bsize = 15

    def form_content(self):
        return {'term': self.request.session.get('apps-sharing-term', '')}

    def get_principal(self, id):
        return ptah.resolve(id)

    def update(self):
        res = super(SharingForm, self).update()

        request = self.request
        context = self.context

        self.roles = [r for r in ptah.get_roles().values() if not r.system]
        self.local_roles = local_roles = context.__local_roles__

        term = request.session.get('apps-sharing-term', '')
        if term:
            self.users = list(ptah.search_principals(term))

        if 'form.buttons.save' in request.POST:
            users = []
            userdata = {}
            for attr, val in request.POST.items():
                if attr.startswith('user-'):
                    userId, roleId = attr[5:].rsplit('-',1)
                    data = userdata.setdefault(str(userId), [])
                    data.append(str(roleId))
                if attr.startswith('userid-'):
                    users.append(str(attr.split('userid-')[-1]))

            for uid in users:
                if userdata.get(uid):
                    local_roles[str(uid)] = userdata[uid]
                elif uid in local_roles:
                    del local_roles[uid]

            context.__local_roles__ = local_roles

        return res

    @form.button('Search', actype=form.AC_PRIMARY)
    def search(self):
        data, error = self.extract()

        if not data['term']:
            self.message('Please specify search term', 'warning')
            return

        self.request.session['apps-sharing-term'] = data['term']
        return HTTPFound(location = self.request.url)


ptah.uiaction(
    ptah.ILocalRolesAware, **{'id': 'view',
                              'title': 'View',
                              'action': '',
                              'category': MANAGE_APP_CATEGORY,
                              'sort_weight': 1.0})

ptah.uiaction(
    ptah.ILocalRolesAware, **{'id': 'sharing',
                              'title': 'Sharing',
                              'action': 'sharing.html',
                              'category': MANAGE_APP_CATEGORY,
                              'sort_weight': 10.0})
