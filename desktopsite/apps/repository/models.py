from django.db import models
from django.contrib.auth.models import User
from desktopsite.apps.repository import managers
from desktopsite.apps.repository.categories import *
from django.contrib import admin
from desktopsite.apps.repository.middleware import threadlocals

class Package(models.Model):
    sysname = models.SlugField("System Name", unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    screenshot = models.ImageField(upload_to="repository/screenshots/", blank=True, null=True)
    url = models.URLField("Homepage", blank=True, null=True)
    maintainer = models.ForeignKey(User)
    category = models.CharField(max_length=100, choices=REPOSITORY_CATEGORIES)
    license = models.CharField(max_length=100)
    license_link = models.URLField("Link to license", help_text="If you are unsure of which license to pick,<br />it is recommended you use the <a href=\"http://www.opensource.org/licenses/afl-3.0.php\">Academic Free License</a>.")
    def get_absolute_url(self):
        return "/repository/packages/%s/" % self.sysname
    def get_versions_desc(self):
        return self.version_set.order_by("-name")
    def get_latest(self):
        try:
            return self.get_versions_desc()[0]
        except IndexError:
            return None
    def user_is_maintainer(self):
        return threadlocals.get_current_user().pk == self.maintainer.pk or threadlocals.get_current_user().is_staff
    def __str__(self):
        return self.name

class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'sysname', 'category', 'maintainer', 'license')
    list_filter = ('category',)
    search_fields = ('name', 'sysname')
    ordering = ('name', 'sysname')

admin.site.register(Package, PackageAdmin)
   
from desktopsite.apps.downloads.models import Release

class Version(models.Model):
    package = models.ForeignKey(Package, blank=True, null=True)
    name = models.CharField(max_length=100, help_text="""<div class="help">Example: 1.2.16-beta2</div>""")
    changelog = models.TextField(help_text="""<div class="help">A list of changes since the last release</div>""")
    #package_url = models.URLField(help_text="""<div class="help">This is a direct url to the package.<br />
    #                                           File sharing sites such as mediafire or rapidshare will not work.<br />
    #                                           If you cannot host the package yourself,<br />
    #                                           it is suggested that you use <a href="http://omploader.org/">Omploader</a>.</div>""")
    package_file = models.FileField(upload_to="repository/packages/",
                                    help_text="The repository will read information from the package, make sure meta.json is accurate")
    creation_date = models.DateTimeField(auto_now=True, editable=False)
    #checksum = models.CharField(max_length=100, help_text="""<div class="help">The md5sum of the package. See <a href="http://www.openoffice.org/dev_docs/using_md5sums.html">this page</a> for details on how to get this.</div>""")
    checksum = models.CharField(max_length=100, editable=False)
    verified_safe = models.BooleanField(default=False)
    compatibility = models.ManyToManyField(Release)
    
    def __str__(self):
        return "%s %s" % (self.package.name, self.name)
    
    def get_absolute_url(self):
        return "/repository/packages/%s/%s/" % (self.package.sysname, self.name)
    def get_rating(self):
        return Rating.objects.score_for_version(self.pk)
    def get_rating_for_user(self):
        try:
            return Rating.objects.get(user=threadlocals.get_current_user(), version=self).score
        except:
            return 0
    def is_new(self):
        import datetime
        three_days_ago = datetime.timedelta(days=-3)
        return (datetime.datetime.now() + three_days_ago) <= self.creation_date
    def is_latest(self):
        return self.package.version_set.order_by("-name")[0].pk == self.pk
    def calc_md5sum(self):
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import hashlib
        m = hashlib.md5()
        f = default_storage.open(self.package_file.path)
        f.open(mode="r")
        while 1:
            buf = f.read(4096)
            if buf == "":
                break;
            m.update(buf)
        f.close()
        self.checksum = m.hexdigest()
        self.save()
       
class VersionAdmin(admin.ModelAdmin):
    list_display = ('package', 'name')
    list_filter = ('verified_safe',)
    search_fields = ('name', 'package__name', 'package__sysname')
    ordering = ('package', 'name')


admin.site.register(Version, VersionAdmin)

class Rating(models.Model):
    version=models.ForeignKey(Version)
    user=models.ForeignKey(User)
    date = models.DateTimeField(editable=False, auto_now_add=True)
    score=models.IntegerField(choices=((1, "1"),(2, "2"),(3, "3"),(4, "4"),(5, "5")))
    
    objects = managers.RatingsManager()
