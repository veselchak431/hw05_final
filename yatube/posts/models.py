from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

POST_STRING_VIEW_LENGTH = 15


class Group(models.Model):
    def __str__(self):
        return self.title

    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группы'
        verbose_name_plural = 'Группы'


class Post(models.Model):

    def __str__(self):
        return self.text[:POST_STRING_VIEW_LENGTH]

    text = models.TextField(verbose_name='текст')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='автор')
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              verbose_name='группа')

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Посты'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)


class Follow(models.Model):
    def __str__(self):
        return f'{self.user} following {self.author}'

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='автор')

    class Meta:
        unique_together = ('user', 'author')


class Comment(models.Model):
    def __str__(self):
        return self.text[:POST_STRING_VIEW_LENGTH]

    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             verbose_name='пост')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comment',
                               verbose_name='автор')
    text = models.TextField(verbose_name='текст')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата публикации')

    class Meta:
        verbose_name = 'Комментарии'
        verbose_name_plural = 'Комментарии'
        ordering = ('post', 'created')
