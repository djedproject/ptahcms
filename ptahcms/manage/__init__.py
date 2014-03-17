# ptah manage api

# pyramid include
def includeme(config):
    # manage templates
    config.add_layer('ptahcms-manage', path='ptahcms:templates/manage')

