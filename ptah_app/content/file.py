""" file content implementation """
import sqlalchemy as sqla
from memphis import view, form

import ptah, ptah_cms, ptah_app
from ptah_app.permissions import AddFile


class File(ptah_cms.Content):

    __tablename__ = 'ptah_app_files'

    __type__ = ptah_cms.Type(
        'file',
        title = 'File',
        description = 'A file in the site.',
        permission = AddFile,
        addview = 'addfile.html',
        )

    blobref = sqla.Column(
        sqla.Unicode,
        info = {'title': 'Data',
                'field_type': 'file'})

    @ptah_cms.action(permission=ptah_cms.ModifyContent)
    def update(self, **data):
        """ Update file content. """
        fd = data.get('blobref')
        if fd:
            blob = ptah.resolve(self.blobref)
            if blob is None:
                blob = ptah_cms.blobStorage.create(self)
                self.blobref = blob.__uri__

            blob.write(fd['fp'].read())
            blob.updateMetadata(
                filename = fd['filename'],
                mimetype = fd['mimetype'])

        self.title = data['title']
        self.description = data['description']

    @ptah_cms.action(permission=ptah_cms.View)
    def data(self):
        """ Download data. """
        blob = ptah.resolve(self.blobref)
        if blob is None:
            raise ptah_cms.NotFound()

        return {'mimetype': blob.mimetype,
                'filename': blob.filename,
                'data': blob.read()}


class FileDownloadView(view.View):
    view.pyramidview('download.html', File, layout=None,
                     permission = ptah_cms.View)

    def render(self):
        data = self.context.data()

        response = self.request.response
        response.content_type = data['mimetype'].encode('utf-8')
        response.headerlist = {
            'Content-Disposition':
            'filename="%s"'%data['filename'].encode('utf-8')}
        response.body = data['data']
        return response


class FileView(FileDownloadView):
    view.pyramidview(context = File,
                     permission = ptah_cms.View)

    template = view.template('ptah_app:templates/file.pt')

    def update(self):
        self.resolve = ptah.resolve

    def render(self):
        if self.request.url.endswith('/'):
            return self.template(
                view = self,
                context = self.context,
                request = self.request)

        return super(FileView, self).render()


class FileAddForm(ptah_app.AddForm):
    view.pyramidview('addfile.html', ptah_cms.IContainer)

    tinfo = File.__type__

    def chooseName(self, **kw):
        filename = kw['blobref']['filename']
        name = filename.split('\\')[-1].split('/')[-1]

        i = 1
        n = name
        while n in self.container:
            i += 1
            n = u'%s-%s'%(name, i)

        return n
