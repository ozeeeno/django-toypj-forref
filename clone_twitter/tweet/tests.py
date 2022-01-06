from django.test import TestCase

from factory.django import DjangoModelFactory

from user.models import User, Follow
from tweet.models import Tweet, Reply, Retweet, UserLike
from django.test import TestCase
from django.db import transaction
from rest_framework import status
from user.serializers import jwt_token_of

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = 'test@test.com'

    @classmethod
    def create(cls, **kwargs):
        user = User.objects.create(**kwargs)
        user.set_password(kwargs.get('password', ''))
        user.save()
        return user


class FollowFactory(DjangoModelFactory):
    class Meta:
        model = Follow

    @classmethod
    def create(cls, **kwargs):
        follow = Follow.objects.create(**kwargs)
        follow.save()
        return follow


class TweetFactory(DjangoModelFactory):
    class Meta:
        model = Tweet
    id = 1

    @classmethod
    def create(cls, **kwargs):
        tweet = Tweet.objects.create(**kwargs)
        tweet.save()
        return tweet


class RetweetFactory(DjangoModelFactory):
    class Meta:
        model = Retweet

    @classmethod
    def create(cls, **kwargs):
        retweet = Retweet.objects.create(**kwargs)
        retweet.save()
        return retweet


class PostTweetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.post_data = {
            'content': 'content',
            # 'media': 'media',
        }

    def test_post_tweet_missing_required_field(self):
        # No content nor media
        data = self.post_data.copy()
        data.pop('content')
        # data.pop('media')
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_tweet_success(self):
        # there are both content and media
        data = self.post_data.copy()
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully write tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)


class DeleteTweetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.author_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.other = UserFactory(
            email='test@email.com',
            user_id='other',
            username='username1',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.other_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.author,
            content = 'content'
        )

        cls.retweet = TweetFactory(
            tweet_type = 'RETWEET',
            author = cls.other,
            retweeting_user = cls.author.user_id,
            content = 'content'
        )

    def test_delete_not_my_tweet(self):
        tweets = Tweet.objects.all()
        tweet = tweets[0]
        retweet = tweets[1]
        response = self.client.delete('/api/v1/tweet/' + str(tweet.id) + '/', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete('/api/v1/tweet/' + str(retweet.id) + '/', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_tweet_wrong_id(self):
        response = self.client.delete('/api/v1/tweet/-1/', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_tweet_success(self):
        tweets = Tweet.objects.all()
        tweet = tweets[0]
        retweet = tweets[1]
        response = self.client.delete('/api/v1/tweet/' + str(tweet.id) + '/', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete('/api/v1/tweet/' + str(retweet.id) + '/', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['message'], "successfully delete tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)


class ReplyTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
            'content': 'content',
            # 'media': 'media',
        }

    def test_reply_wrong_id(self):
        data = self.post_data.copy()
        data['id'] = -1
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reply_missing_required_field(self):
        # No tweet_id
        data = self.post_data.copy()
        data.pop('id')
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # No content nor media
        data = self.post_data.copy()
        data.pop('content')
        # data.pop('media')
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_tweet_success(self):
        # there are both content and media
        data = self.post_data.copy()
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully reply tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 1)

    def test_reply_delete(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        # delete replied tweet
        response = self.client.delete('/api/v1/tweet/' + str(self.tweet.id) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 1)

        # delete replying tweet
        response = self.client.delete('/api/v1/tweet/' + str(self.tweet.id + 1) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 0)


class RetweetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
        }

    def test_retweet_wrong_id(self):
        data = self.post_data.copy()
        data['id'] = -1
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retweet_missing_required_field(self):
        # No tweet_id
        data = self.post_data.copy()
        data.pop('id')
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retweet_success(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully do retweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 1)

    def test_retweet_multiple_times(self):
        data = self.post_data.copy()
        self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        with transaction.atomic():
            response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = response.json()
        self.assertEqual(data['message'], "you already retweeted this tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 1)

    def test_retweet_delete(self):
        data = self.post_data.copy()
        self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        # delete retweeting tweet
        response = self.client.delete('/api/v1/tweet/' + str(self.tweet.id + 1) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)

        # delete retweeted tweet
        data = self.post_data.copy()
        self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        response = self.client.delete('/api/v1/tweet/' + str(self.tweet.id) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)


class RetweetCancelTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.other = UserFactory(
            email='test@email.com',
            user_id='other',
            username='username1',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.other_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        cls.retweeting = TweetFactory(
            tweet_type = 'RETWEET',
            author = cls.user,
            content = 'content',
            retweeting_user = cls.user.user_id
        )

        cls.retweet = RetweetFactory(
            retweeted = cls.tweet,
            retweeting = cls.retweeting,
            user = cls.user
        )

        tweets = Tweet.objects.all()
        cls.source_tweet = tweets[0]


    def test_retweet_cancel_wrong_source_id(self):
        response = self.client.delete('/api/v1/retweet/-1/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retweet_cancel_does_not_exist(self):
        self.client.delete('/api/v1/tweet/' + str(self.source_tweet.id + 1) + '/', HTTP_AUTHORIZATION=self.user_token)

        response = self.client.delete('/api/v1/retweet/' + str(self.source_tweet.id) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data['message'], "you have not retweeted this tweet")

    def test_retweet_cancel_success(self):
        response = self.client.delete('/api/v1/retweet/' + str(self.source_tweet.id) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['message'], "successfully cancel retweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)


class TweetDetailTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username1',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user2 = UserFactory(
            email='test@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.user2_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user1,
            content = 'content'
        )


    def test_get_tweet_wrong_pk(self):
        response = self.client.get('/api/v1/tweet/0/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_tweet_pk(self):
        tweets = Tweet.objects.all()
        tweet = tweets[0]

        self.client.post('/api/v1/reply/', data={'id': tweet.id, 'content': 'content'}, content_type='application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.client.post('/api/v1/reply/', data={'id': tweet.id + 1, 'content': 'content'}, content_type='application/json', HTTP_AUTHORIZATION=self.user2_token)
        self.client.post('/api/v1/reply/', data={'id': tweet.id + 1, 'content': 'content'}, content_type='application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.client.post('/api/v1/retweet/', data={'id': tweet.id + 1}, content_type='application/json', HTTP_AUTHORIZATION=self.user2_token)

        response = self.client.get('/api/v1/tweet/' + str(tweet.id+1) + '/', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn('id', data)

        author = data['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username1')
        self.assertEqual(author['user_id'], 'user1_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(data['tweet_type'], 'REPLY')
        self.assertEqual(data['retweeting_user'], '')
        self.assertEqual(data['reply_to'], 'user1_id')
        self.assertEqual(data['content'], 'content')
        self.assertEqual(data['media'], [])
        self.assertIn('written_at', data)
        self.assertEqual(data['retweets'], 1)
        self.assertFalse(data['user_retweet'])
        self.assertEqual(data['quotes'], 0)
        self.assertEqual(data['likes'], 0)
        self.assertFalse(data['user_like'])


        replied_tweet = data['replied_tweet']
        self.assertIsNotNone(replied_tweet)

        self.assertIn('id', replied_tweet)

        author = replied_tweet['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username1')
        self.assertEqual(author['user_id'], 'user1_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(replied_tweet['tweet_type'], 'GENERAL')
        self.assertEqual(replied_tweet['retweeting_user'], '')
        self.assertEqual(replied_tweet['reply_to'], '')
        self.assertEqual(replied_tweet['content'], 'content')
        self.assertEqual(replied_tweet['media'], [])
        self.assertIn('written_at', replied_tweet)
        self.assertEqual(replied_tweet['replies'], 1)
        self.assertEqual(replied_tweet['retweets'], 0)
        self.assertFalse(replied_tweet['user_retweet'])
        self.assertEqual(replied_tweet['likes'], 0)
        self.assertFalse(replied_tweet['user_like'])

        replying_tweets = data['replying_tweets']
        self.assertIsNotNone(replying_tweets)
        self.assertEqual(len(replying_tweets), 2)
        replying_tweet = replying_tweets[0]

        self.assertIn('id', replying_tweet)

        author = replying_tweet['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username2')
        self.assertEqual(author['user_id'], 'user2_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(replying_tweet['content'], 'content')
        self.assertEqual(replying_tweet['media'], [])
        self.assertIn('written_at', replying_tweet)
        self.assertEqual(replying_tweet['replies'], 0)
        self.assertEqual(replying_tweet['retweets'], 0)
        self.assertFalse(replying_tweet['user_retweet'])
        self.assertEqual(replying_tweet['likes'], 0)
        self.assertFalse(replying_tweet['user_like'])


        response = self.client.get('/api/v1/tweet/' + str(tweet.id + 1) + '/', HTTP_AUTHORIZATION=self.user2_token)
        data = response.json()

        self.assertTrue(data['user_retweet'])


class LikeTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
        }

    def test_like_wrong_id(self):
        data = self.post_data.copy()
        data['id'] = -1
        response = self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_missing_required_field(self):
        # No tweet_id
        data = self.post_data.copy()
        data.pop('id')
        response = self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_like_success(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully like")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        user_like_count = UserLike.objects.count()
        self.assertEqual(user_like_count, 1)

    def test_like_multiple_times(self):
        data = self.post_data.copy()
        self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        with transaction.atomic():
            response = self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = response.json()
        self.assertEqual(data['message'], "you already liked this tweet")

        user_like_count = UserLike.objects.count()
        self.assertEqual(user_like_count, 1)

    def test_like_delete(self):
        data = self.post_data.copy()
        self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        # delete liked tweet
        response = self.client.delete('/api/v1/tweet/' + str(data['id']) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)
        user_like_count = UserLike.objects.count()
        self.assertEqual(user_like_count, 0)


class LikeCancelTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.other = UserFactory(
            email='test@email.com',
            user_id='other',
            username='username1',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.other_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
        }

    def test_like_cancel_wrong_source_id(self):
        response = self.client.delete('/api/v1/like/-1/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_cancel_does_not_exist(self):
        data = self.post_data.copy()
        response = self.client.delete('/api/v1/like/' + str(data['id']) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data['message'], "you have not liked this tweet")

    def test_like_cancel_success(self):
        data = self.post_data.copy()
        self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        response = self.client.delete('/api/v1/like/' + str(data['id']) + '/', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['message'], "successfully cancel like")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        user_like_count = UserLike.objects.count()
        self.assertEqual(user_like_count, 0)


class HomeTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username1',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user2 = UserFactory(
            email='test@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.user2_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.user3 = UserFactory(
            email='test3@email.com',
            user_id='user3_id',
            username='username3',
            password='password',
            phone_number='010-1234-2222'
        )
        cls.user3_token = 'JWT ' + jwt_token_of(User.objects.get(email='test3@email.com'))

        cls.follow = FollowFactory(
            following = cls.user1,
            follower = cls.user2
        )

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user1,
            content = 'content'
        )

    def test_get_home(self):
        # No following & No tweet
        response = self.client.get('/api/v1/home/', HTTP_AUTHORIZATION=self.user3_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        user = data['user']
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'username3')
        self.assertEqual(user['user_id'], 'user3_id')
        # self.assertIsNone(user['profile_img'])

        tweets = data['tweets']
        self.assertIsNotNone(tweets)
        self.assertEqual(tweets, [])

        # No following
        response = self.client.get('/api/v1/home/', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        user = data['user']
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'username1')
        self.assertEqual(user['user_id'], 'user1_id')
        # self.assertIsNone(user['profile_img'])

        tweets = data['tweets']
        self.assertIsNotNone(tweets)
        tweet = tweets[0]

        self.assertIn('id', tweet)

        author = tweet['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username1')
        self.assertEqual(author['user_id'], 'user1_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(tweet['tweet_type'], 'GENERAL')
        self.assertEqual(tweet['retweeting_user'], '')
        self.assertEqual(tweet['reply_to'], '')
        self.assertEqual(tweet['content'], 'content')
        self.assertEqual(tweet['media'], [])
        self.assertIn('written_at', tweet)
        self.assertEqual(tweet['replies'], 0)
        self.assertEqual(tweet['retweets'], 0)
        self.assertFalse(tweet['user_retweet'])
        self.assertEqual(tweet['likes'], 0)
        self.assertFalse(tweet['user_like'])

        # Following O
        data = {
            'content': 'content22',
            # 'media': 'media',
        }
        self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user2_token)

        tweets = Tweet.objects.all()
        tweet = tweets[1]

        data = {'id': tweet.id}
        self.client.post('/api/v1/like/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user2_token)

        response = self.client.get('/api/v1/home/', HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        user = data['user']
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'username2')
        self.assertEqual(user['user_id'], 'user2_id')
        # self.assertIsNone(user['profile_img'])

        tweets = data['tweets']
        self.assertIsNotNone(tweets)
        my_tweet = tweets[0]
        following_tweet = tweets[1]

        self.assertIn('id', my_tweet)

        author = my_tweet['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username2')
        self.assertEqual(author['user_id'], 'user2_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(my_tweet['tweet_type'], 'GENERAL')
        self.assertEqual(my_tweet['retweeting_user'], '')
        self.assertEqual(my_tweet['reply_to'], '')
        self.assertEqual(my_tweet['content'], 'content22')
        self.assertEqual(my_tweet['media'], [])
        self.assertIn('written_at', my_tweet)
        self.assertEqual(my_tweet['replies'], 0)
        self.assertEqual(my_tweet['retweets'], 0)
        self.assertFalse(my_tweet['user_retweet'])
        self.assertEqual(my_tweet['likes'], 1)
        self.assertTrue(my_tweet['user_like'])

        self.assertIn('id', following_tweet)

        author = following_tweet['author']
        self.assertIsNotNone(author)
        self.assertEqual(author['username'], 'username1')
        self.assertEqual(author['user_id'], 'user1_id')
        # self.assertIsNone(author['profile_img'])

        self.assertEqual(following_tweet['tweet_type'], 'GENERAL')
        self.assertEqual(following_tweet['retweeting_user'], '')
        self.assertEqual(following_tweet['reply_to'], '')
        self.assertEqual(following_tweet['content'], 'content')
        self.assertEqual(following_tweet['media'], [])
        self.assertIn('written_at', following_tweet)
        self.assertEqual(following_tweet['replies'], 0)
        self.assertEqual(following_tweet['retweets'], 0)
        self.assertFalse(following_tweet['user_retweet'])
        self.assertEqual(following_tweet['likes'], 0)
        self.assertFalse(following_tweet['user_like'])
