from django.contrib.auth import get_user_model
from django.db.models.fields.files import ImageFieldFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache
from posts.models import Group, Post, Follow
from posts.views import POSTS_ON_PAGE

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):

        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Вторая группа',
            slug='second-group',
            description='группа для проверки на разных страницах',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.png',
            content=self.small_gif,
            content_type='image/gif'
        )

        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
            image=self.uploaded

        )

        self.second_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост 2',
            group=self.second_group)
        cache.clear()

    def test_pages_uses_correct_template(self):

        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={
                        'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': 'HasNoName'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(response.context.get('title'),
                         'Последние обновления на сайте')
        for post in response.context['page_obj'].object_list:
            if post == self.post:
                image = post.image
                self.assertIsInstance(image, ImageFieldFile)
                self.assertEqual(image.file.read(), self.small_gif)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:profile',
                    kwargs={'username': 'HasNoName'})))
        self.assertEqual(response.context.get('title'),
                         'Профайл пользователя HasNoName')
        for post in response.context['page_obj'].object_list:
            if post == self.post:
                image = post.image
                self.assertIsInstance(image, ImageFieldFile)
                self.assertEqual(image.file.read(), self.small_gif)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'})))
        self.assertEqual(response.context.get('title'),
                         'группа Тестовая группа')
        image = response.context['page_obj'][0].image
        self.assertIsInstance(image, ImageFieldFile)
        self.assertEqual(image.file.read(), self.small_gif)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post'), self.post)
        self.assertEqual(response.context.get('posts_count'),
                         Post.objects.filter(author=self.post.author).count())

        image = response.context['post'].image
        self.assertIsInstance(image, ImageFieldFile)
        self.assertEqual(image.file.read(), self.small_gif)

    def page_with_createpost_template_show_correct_context(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_pages_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:post_create')))
        self.page_with_createpost_template_show_correct_context(response)

    def test_edit_post_pages_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})))
        self.page_with_createpost_template_show_correct_context(response)

    def test_post_with_group_on_page(self):
        """Пост с группой находится на страницах index, group,profile"""
        pages_names_tuple = (reverse('posts:index'),
                             reverse('posts:group_list',
                                     kwargs={'slug': self.second_group.slug}),
                             reverse('posts:profile',
                                     kwargs={'username': self.user})
                             )
        for page in pages_names_tuple:
            response = (self.authorized_client.get(page))

            self.assertIn(self.second_post,
                          response.context.get('page_obj').object_list)


class PaginatorViewsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):

        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')

        self.authorized_client = Client()

        self.authorized_client.force_login(self.user)

        self.count_of_posts = 15
        self.count_of_posts_seconds_page = self.count_of_posts % POSTS_ON_PAGE

        posts = (Post(author=self.user,
                      text=str(i),
                      group=self.group)
                 for i in range(self.count_of_posts))
        Post.objects.bulk_create(posts, self.count_of_posts)
        cache.clear()

    def test_first_index_page_contains_ten_records(self):

        response = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         POSTS_ON_PAGE)

    def test_second_index_page_contains_three_records(self):

        response = (self.authorized_client.get(
            reverse('posts:index') + '?page=2'))
        self.assertEqual(len(response.context.get(
            'page_obj').object_list), self.count_of_posts_seconds_page)

    def test_first_group_page_contains_ten_records(self):

        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         POSTS_ON_PAGE)

    def test_second_group_page_contains_three_records(self):

        response = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2'))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         self.count_of_posts_seconds_page)

    def test_first_profile_page_contains_ten_records(self):

        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'HasNoName'})))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         POSTS_ON_PAGE)

    def test_second_profile_page_contains_three_records(self):

        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'HasNoName'}) + '?page=2'))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         self.count_of_posts_seconds_page)


class CacheViewsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )

    def test_posts_cache_index(self):
        response = (self.authorized_client.get(reverse('posts:index')))
        context = response.context
        self.post.delete()
        response = (self.authorized_client.get(reverse('posts:index')))
        context_after_delete = response.context
        self.assertEqual(context, context_after_delete)
        cache.clear()
        response = (self.authorized_client.get(reverse('posts:index')))
        context_after_clean = response.context
        self.assertNotEqual(context, context_after_clean)


class CFollowViewsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )

    def test_posts_authorized_index(self):
        response = (self.authorized_client.get(reverse('posts:index')))
        context = response.context
        self.post.delete()
        response = (self.authorized_client.get(reverse('posts:index')))
        context_after_delete = response.context
        self.assertEqual(context, context_after_delete)
        cache.clear()
        response = (self.authorized_client.get(reverse('posts:index')))
        context_after_clean = response.context
        self.assertNotEqual(context, context_after_clean)


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        self.second_user = User.objects.create_user(username='SecondUser')
        self.authorized_second_client = Client()
        self.authorized_second_client.force_login(self.second_user)

    def test_views_authorized_client_try_follow(self):
        follow_count = Follow.objects.all().count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.second_user}))
        follow_count_after = Follow.objects.all().count()
        self.assertEqual(follow_count + 1, follow_count_after)

    def test_views_authorized_client_try_unfollow(self):
        follow_count = Follow.objects.all().count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.second_user}))
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.second_user}))

        follow_count_after = Follow.objects.all().count()
        self.assertEqual(follow_count, follow_count_after)

    def test_views_following_user_get_new_post(self):
        url = reverse('posts:profile_follow',
                      kwargs={'username': self.second_user})
        response = self.authorized_client.get(url)
        self.follow_post = Post.objects.create(
            author=self.second_user,
            text='Тестовый пост для пдписки',
        )
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)
        posts = response.context.get('page_obj').object_list
        self.assertIn(self.follow_post, posts)

    def test_views_unfollowing_user_not_get_new_post(self):
        url = reverse('posts:profile_follow',
                      kwargs={'username': self.second_user})
        self.follow_post = Post.objects.create(
            author=self.second_user,
            text='Тестовый пост для пдписки',
        )
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)
        posts = response.context.get('page_obj').object_list
        self.assertNotIn(self.follow_post, posts)
