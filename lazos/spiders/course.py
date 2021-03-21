from datetime import datetime
from pprint import pprint
from scrapy.linkextractors import LinkExtractor
from urllib.parse import parse_qs
import scrapy
import urllib.parse as urlparse

now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

def _param(url, param):
    parsed = urlparse.urlparse(url)
    value = parse_qs(parsed.query).get(param)
    return value[0] if value else None

def _add_param_perpage(url):
    return f'{url}&&perpage=200'

class CourseSpider(scrapy.Spider):
    name = 'course'
    main_domain = 'lazos.neuquen.edu.ar'
    main_url = f'https://{main_domain}'
    allowed_domains = [main_domain]
    start_urls = [f'{main_url}/login/index.php']

    custom_settings = {
        'FEEDS': {
            f'csv/{name}-{now}.csv': {
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False,
            }
        },
        'LOG_FILE': f'log/{name}.log',
        # 'CLOSESPIDER_PAGECOUNT': 10,
    }

    link_extractor_category = LinkExtractor(
        restrict_css='h3.categoryname',
        process_value=_add_param_perpage
    )
    link_extractor_course = LinkExtractor(
        restrict_css='.coursename',
        # process_value=_add_param_perpage
    )

    def parse(self, response):
        username = '41438786'
        password = 'mississippi1'
        formdata = dict(username=username, password=password)
        return scrapy.FormRequest.from_response(
            response,
            formdata=formdata,
            callback=self.follow_after_login
        )

    def follow_after_login(self, response):
        params = 'categoryid=2551'
        url = f'{self.main_url}/course/index.php?{params}'
        return scrapy.Request(url=url, callback=self.parse_categories)

    def parse_categories(self, response):
        categories = self.link_extractor_category.extract_links(response)
        for category in categories:
            id_ = _param(category.url, 'categoryid') or 0
            name = category.text\
                .replace('CPEM 55', '')\
                .strip()\
                .lower()
            cb_kwargs = dict(category_id=id_, category_name=name)
            yield response.follow(
                url=category,
                callback=self.parse_courses,
                cb_kwargs=cb_kwargs
            )

    def parse_courses(self, response, category_id, category_name):
        courses = self.link_extractor_course.extract_links(response)
        for course in courses:
            id_ = _param(course.url, 'id') or 0
            name = course.text\
                .replace('CPEM 55', '')\
                .replace(category_name, '')\
                .strip()\
                .lower()
            yield {
                'id': id_,
                'name': name,
                'group_name': category_name,
                'group_id': category_id,
           }

