# -*- coding: utf-8 -*-
import json
import logging
import re
from collections import OrderedDict
from datetime import datetime

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import public_proto_pb2
from constants import API_URL, LOGIN_OAUTH, LOGIN_URL, PTC_CLIENT_SECRET

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class AuthUtil(object):
    def __init__(self, username, password, location, login='ptc'):
        """
        Performs login and prints some basic profile info

        :param username: Login username
        :param password: Login password
        :param location: A LocationUtil object
        :param login: login location either 'ptc' or 'google'
        """
        self.session = requests.session()
        self.session.headers.update({'User-Agent': 'Niantic App'})
        self.session.verify = False

        # This is the staring location
        self.location = location

        if login == 'google':
            glogin = self.login_google(username, password)
            if glogin and glogin.get('id_token'):
                self.access_token = glogin.get('id_token')
            else:
                raise Exception('Failed to get Google login token')
        else:
            self.access_token = self.login_pokemon(username, password)

        if self.access_token is None:
            raise Exception('[-] Wrong username/password?')
        print('[+] RPC Session Token: {} ...'.format(self.access_token[:25]))

        self.api_endpoint = self.get_api_endpoint(self.access_token, login)
        if self.api_endpoint is None:
            raise Exception('[-] RPC server offline')
        print('[+] Received API endpoint: {}'.format(self.api_endpoint))

        profile = self.get_profile(self.api_endpoint, self.access_token, login)
        if profile is not None:
            print('[+] Login successful')

            profile = profile.payload[0].profile
            print('[+] Username: {}'.format(profile.username))

            creation_time = datetime.fromtimestamp(int(profile.creation_time) / 1000)
            print('[+] You are playing Pokemon Go since: {}'.format(
                creation_time.strftime('%Y-%m-%d %H:%M:%S'),
            ))

            print('[+] Poke Storage: {}'.format(profile.poke_storage))
            print('[+] Item Storage: {}'.format(profile.item_storage))

            for curr in profile.currency:
                print('[+] {}: {}'.format(curr.type, curr.amount))
        else:
            raise Exception('[-] Could not retrieve profile')

    def login_pokemon(self, user, passw):
        """
        Perform login with Pokemon Trainer Club
        Returns access token

        :param user:
        :param passw:
        :return:
        """
        print '[!] doing login for:', user
        try:
            head = {'User-Agent': 'niantic'}
            r = self.session.get(LOGIN_URL, headers=head)
            jdata = json.loads(r.content)

            new_url = LOGIN_URL
            data = OrderedDict(
                [('lt', jdata['lt']), ('execution', jdata['execution']), ('_eventId', 'submit'), ('username', user),
                 ('password', passw)])

            r1 = self.session.post(new_url, data=data, headers=head, allow_redirects=False)
            raw_ticket = r1.headers['Location']
            if 'errors' in r1.content:
                print json.loads(r1.content)['errors'][0].replace('&#039;', '\'')
                return None
            ticket = re.sub('.*ticket=', '', raw_ticket)

            data1 = OrderedDict([('client_id', 'mobile-app_pokemon-go'),
                                 ('redirect_uri', 'https://www.nianticlabs.com/pokemongo/error'),
                                 ('client_secret', PTC_CLIENT_SECRET),
                                 ('grant_type', 'refresh_token'), ('code', ticket)])

            r2 = self.session.post(LOGIN_OAUTH, data=data1)
            access_token = re.sub('.*en=', '', r2.content)
            access_token = re.sub('.com.*', '.com', access_token)
            return access_token
        except Exception:
            logging.exception('[-] pokemon attacking the login server')
            return None

    def login_google(self, email, passw):
        """
        A very messy way of logging in with Google
        Returns access token

        :param email:
        :param passw:
        :return:
        """
        try:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) '
                              'Mobile/12H143'})
            first = 'https://accounts.google.com/o/oauth2/auth?client_id=' \
                    '848232511240-73ri3t7plvk96pj4f85uj8otdat2alem.apps.googleusercontent.com&redirect_uri=' \
                    'urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&scope=openid%20email%20https%3A%2F%2F' \
                    'www.googleapis.com%2Fauth%2Fuserinfo.email'
            second = 'https://accounts.google.com/AccountLoginInfo'
            third = 'https://accounts.google.com/signin/challenge/sl/password'
            last = 'https://accounts.google.com/o/oauth2/token'
            r = self.session.get(first)

            GALX = re.search('<input type="hidden" name="GALX" value=".*">', r.content)
            gxf = re.search('<input type="hidden" name="gxf" value=".*:.*">', r.content)
            cont = re.search('<input type="hidden" name="continue" value=".*">', r.content)

            GALX = re.sub('.*value="', '', GALX.group(0))
            GALX = re.sub('".*', '', GALX)

            gxf = re.sub('.*value="', '', gxf.group(0))
            gxf = re.sub('".*', '', gxf)

            cont = re.sub('.*value="', '', cont.group(0))
            cont = re.sub('".*', '', cont)

            data1 = {'Page': 'PasswordSeparationSignIn',
                     'GALX': GALX,
                     'gxf': gxf,
                     'continue': cont,
                     'ltmpl': 'embedded',
                     'scc': '1',
                     'sarp': '1',
                     'oauth': '1',
                     'ProfileInformation': '',
                     '_utf8': '?',
                     'bgresponse': 'js_disabled',
                     'Email': email,
                     'signIn': 'Next'}
            r1 = self.session.post(second, data=data1)

            profile = re.search('<input id="profile-information" name="ProfileInformation" type="hidden" value=".*">',
                                r1.content)
            gxf = re.search('<input type="hidden" name="gxf" value=".*:.*">', r1.content)

            gxf = re.sub('.*value="', '', gxf.group(0))
            gxf = re.sub('".*', '', gxf)

            profile = re.sub('.*value="', '', profile.group(0))
            profile = re.sub('".*', '', profile)

            data2 = {'Page': 'PasswordSeparationSignIn',
                     'GALX': GALX,
                     'gxf': gxf,
                     'continue': cont,
                     'ltmpl': 'embedded',
                     'scc': '1',
                     'sarp': '1',
                     'oauth': '1',
                     'ProfileInformation': profile,
                     '_utf8': '?',
                     'bgresponse': 'js_disabled',
                     'Email': email,
                     'Passwd': passw,
                     'signIn': 'Sign in',
                     'PersistentCookie': 'yes'}
            r2 = self.session.post(third, data=data2)
            fourth = r2.history[len(r2.history) - 1].headers['Location'].replace('amp%3B', '').replace('amp;', '')
            r3 = self.session.get(fourth)

            client_id = re.search('client_id=.*&from_login', fourth)
            client_id = re.sub('.*_id=', '', client_id.group(0))
            client_id = re.sub('&from.*', '', client_id)

            state_wrapper = re.search('<input id="state_wrapper" type="hidden" name="state_wrapper" value=".*">',
                                      r3.content)
            state_wrapper = re.sub('.*state_wrapper" value="', '', state_wrapper.group(0))
            state_wrapper = re.sub('"><input type="hidden" .*', '', state_wrapper)

            connect_approve = re.search(
                '<form id="connect-approve" action=".*" method="POST" style="display: inline;">', r3.content)
            connect_approve = re.sub('.*action="', '', connect_approve.group(0))
            connect_approve = re.sub('" me.*', '', connect_approve)

            data3 = OrderedDict([('bgresponse', 'js_disabled'), ('_utf8', '☃'), ('state_wrapper', state_wrapper),
                                 ('submit_access', 'true')])
            r4 = self.session.post(connect_approve.replace('amp;', ''), data=data3)

            code = re.search('<input id="code" type="text" readonly="readonly" value=".*" style=".*" onclick=".*;" />',
                             r4.content)
            code = re.sub('.*value="', '', code.group(0))
            code = re.sub('" style.*', '', code)

            data4 = {'client_id': client_id,
                     'client_secret': 'NCjF1TLi2CcY6t5mt0ZveuL7',
                     'code': code,
                     'grant_type': 'authorization_code',
                     'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                     'scope': 'openid email https://www.googleapis.com/auth/userinfo.email'}
            r5 = self.session.post(last, data=data4)
            return json.loads(r5.content)
        except Exception:
            print '[-] problem in google login..'
            return None

    def api_req(self, api_endpoint, access_token, req, ltype):
        """
        Magical Voodoo

        :param api_endpoint:
        :param access_token:
        :param req:
        :param ltype:
        :return:
        """
        try:
            p_req = public_proto_pb2.RequestEnvelop()
            p_req.unknown1 = 2
            p_req.rpc_id = 8145806132888207460

            p_req.requests.MergeFrom(req)

            p_req.latitude, p_req.longitude, p_req.altitude = self.location.latitude, self.location.longitude, \
                self.location.altitude

            p_req.unknown12 = 989
            p_req.auth.provider = ltype
            p_req.auth.token.contents = access_token
            p_req.auth.token.unknown13 = 59
            protobuf = p_req.SerializeToString()

            r = self.session.post(api_endpoint, data=protobuf, verify=False, timeout=3)

            p_ret = public_proto_pb2.ResponseEnvelop()
            p_ret.ParseFromString(r.content)
            return p_ret
        except Exception:
            logging.exception('Something went wrong')
            return None

    def get_api_endpoint(self, access_token, ltype):
        """
        Magical Voodoo

        :param access_token:
        :param ltype:
        :return:
        """
        req = public_proto_pb2.RequestEnvelop()

        req1 = req.requests.add()
        req1.type = 2
        req2 = req.requests.add()
        req2.type = 126
        req3 = req.requests.add()
        req3.type = 4
        req4 = req.requests.add()
        req4.type = 129
        req5 = req.requests.add()
        req5.type = 5
        req5.message.unknown4 = "4a2e9bc330dae60e7b74fc85b98868ab4700802e"

        p_ret = self.api_req(API_URL, access_token, req.requests, ltype)

        try:
            return ('https://%s/rpc' % p_ret.api_url)
        except Exception:
            logging.exception('Something went wrong')
            return None

    def get_profile(self, api_endpoint, access_token, ltype):
        """
        Get the POGO user profile

        :param api_endpoint:
        :param access_token:
        :param ltype:
        :return:
        """
        req = public_proto_pb2.RequestEnvelop()

        req1 = req.requests.add()
        req1.type = 2

        return self.api_req(api_endpoint, access_token, req.requests, ltype)
