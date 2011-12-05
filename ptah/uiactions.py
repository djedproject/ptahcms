""" ui actions """
import ptah
from ptah import config
from zope.interface import implementer, providedBy, Interface


class IAction(Interface):
    """ marker interface for actions """


@implementer(IAction)
class Action(object):
    """ UI Action implementation """

    id = ''
    title = ''
    description = ''
    category = ''
    action = ''
    action_factory = None
    condition = None
    permission = None
    sort_weight = 1.0,
    data = None

    def __init__(self, id='', **kw):
        self.id = id
        self.__dict__.update(kw)

    def url(self, context, request, url=''):
        if self.action_factory is not None:
            return self.action_factory(context, request)

        if self.action.startswith('/'):
            return '%s%s'%(request.application_url, self.action)
        else:
            return '%s%s'%(url, self.action)

    def check(self, context, request):
        if self.permission:
            if not ptah.check_permission(
                self.permission, context, request):
                return False

        if self.condition is not None:
            return self.condition(context, request)

        return True


def uiaction(context, id, title, description='',
             action='', condition=None, permission=None,
             category='', sort_weight = 1.0, **kw):

    kwargs = {'id': id,
              'title': title,
              'description': description,
              'category': category,
              'condition': condition,
              'permission': permission,
              'sort_weight': sort_weight,
              'data': kw}

    if callable(action):
        kwargs['action_factory'] = action
    else:
        kwargs['action'] = action

    ac = Action(**kwargs)
    info = config.DirectiveInfo()

    info.attach(
        config.Action(
            lambda cfg, id, category, context, ac: \
                cfg.registry.registerAdapter(\
                   ac, (context,), IAction, '%s-%s'%(category, id)),
            (id, category, context, ac,),
            discriminator = ('ptah-cms:ui-action', id, context, category))
        )


def list_uiactions(content, request, category=''):
    url = request.resource_url(content)

    actions = []
    for name, action in request.registry.adapters.lookupAll(
        (providedBy(content),), IAction):
        if (action.category == category) and action.check(content, request):
            actions.append(
                (action.sort_weight,
                 {'id': action.id,
                  'url': action.url(content, request, url),
                  'title': action.title,
                  'description': action.description,
                  'data': action.data}))

    return [ac for _w, ac in sorted(actions)]