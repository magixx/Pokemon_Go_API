import argparse
from getpass import getpass

from auth_util import AuthUtil
from location_util import LocationUtil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="Login", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)
    parser.add_argument("-t", "--type", help="google/ptc", required=True)
    parser.add_argument("-l", "--location", help="Location", required=True)
    parser.add_argument("-d", "--distance", help="Distance", required=True)
    args = parser.parse_args()
    if not args.username:
        args.username = getpass("Username: ")
    if not args.password:
        args.password = getpass("Password: ")

    start_location = LocationUtil(args.location)
    authentication = AuthUtil(args.username, args.password, start_location, login='ptc')

if __name__ == '__main__':
    main()
