from django.contrib.sites.models import Site
from django.contrib.syndication.feeds import Feed
from models import Post


SITE = Site.objects.get_current()

class LatestPosts(Feed):
    title = str(SITE) + ' Latest Discussions'
    link = "/forum/"
    description = "The latest contributions to discussions."

    title_template = "snapboard/feeds/latest_title.html"
    description_template = "snapboard/feeds/latest_description.html"

    def items(self):
        # we should only return the non-private messages
        return Post.objects.filter(private__exact=None, censor__exact=False).order_by('-odate')[:20]


# vim: ai ts=4 sts=4 et sw=4
