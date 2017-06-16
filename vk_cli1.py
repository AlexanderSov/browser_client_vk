""" Cli_client for vk.com.

Allows you to change the photo,
read the desired number of news,
chat with a friend (using a friend's ID).

"""

import getpass
from multiprocessing import Process, Value

import requests
import vk
import getch

from time import ctime, sleep


input_state = Value('i', 0)


def do_connection():
    user_login = input('Input phone or email: ')
    user_password = getpass.getpass('Input password: ')
    app_id = input('Input APP_ID: ')  # ID created application
    scope = 'friends,photos,audio,messages,wall'
    session = vk.AuthSession(app_id=app_id, user_login=user_login,
                             user_password=user_password,
                             scope=scope
                             )
    api = vk.API(session)
    return api


def change_photo(api):
    photo_location = input("Enter the photo location: ")
    url = api.photos.getOwnerPhotoUploadServer(owner_id=1)
    file = {'photo': open(photo_location, 'rb')}
    r = requests.post(url['upload_url'], files=file)
    api.photos.saveOwnerPhoto(server=str(r.json()['server']),
                              photo=r.json()['photo'],
                              hash=r.json()['hash']
                              )


def read_news(api):
    amount_news = input("Enter number of news: ")
    news = api.newsfeed.get(count=amount_news)
    for ind, i in enumerate(news['items']):
        news_date = ctime(i['date'])
        source_id = i['source_id']
        try:
            news_text = i['text']
            post_id = i['post_id']
            news_url = 'https://vk.com/feed?w=wall{0}_{1}'.format(source_id,
                                                                  post_id)
        except KeyError:
            print(news['items'].index(i)+1,
                  "No post: advertisement", sep='\n')
        else:
            print(ind, news_url,
                  news_date, news_text, sep='\n')


message_text = ''


def write_messages(api, user_id):
    print("Enter 'exit()' to exit")
    while True:
        msymbol = ''
        global message_text
        message_text = ''
        while msymbol != '\n':
            msymbol = getch.getche()
            message_text += msymbol
            input_state.value = True
        input_state.value = False
        if message_text != 'exit()':
            api.messages.send(user_id=user_id, message=message_text)
            print(list_of_message)
        else:
            raise SystemExit


list_of_message = []


def output_server_answer(updates, user_id):
    if len(updates) > 0:
        if type(updates[0]) == int:
            updates = list(updates)
        for i in updates:
            if i[0] == 4 and i[3] == user_id:
                if bin(i[2])[-2] == '1':
                    sender = "I: "
                else:
                    sender = '{}'.format(user_id)
                message1 = '{0}'.format(ctime(i[4])) + ' ' + sender + i[-1]
                if not input_state.value:
                    print(message1)
                else:
                    global list_of_message
                    list_of_message.append(message1)


cancel_get_poll = True


def get_poll(api, user_id):
    global cancel_get_poll

    cancel_get_poll = True
    history = api.messages.getHistory(count=50, user_id=user_id)
    h1 = []
    for i in history:
        if type(i) == dict:
            h1.append(str(ctime(i['date'])) + ' ' + str(i['from_id'])
                      + ': ' + i['body'])
        else:
            pass
    for i in range(len(h1) - 1, 0, -1):
        print(h1[i])
    # Оповещения от LongPollServer

    session_data = api.messages.getLongPollServer()
    while cancel_get_poll:

        r = requests.get('https://{0}?act=a_check&key={1}&ts={2}&wait=5&\
            mode=128&version=1'.format(session_data['server'],
                                       session_data['key'],
                                       session_data['ts'])
                         )

        if r.json()['ts']:

            session_data['ts'] = r.json()['ts']
            output_server_answer(updates=r.json()['updates'], user_id=user_id)
            global list_of_message
            if list_of_message != [] and input_state.value == False:
                for m in list_of_message:
                    print(m)
                list_of_message = []
        else:
            session_data = api.messages.getLongPollServer()


def main(choice=''):
    api = do_connection()
    while choice != '4':
        print("1. Change photo", "2. Read news",
              "3. Write massege", "4. Exit", sep='\n'
              )
        choice = input("Enter number: ")
        if choice == '1':
            change_photo(api)
        elif choice == '2':
            read_news(api)
        elif choice == '3':
            user_id = int(input("Enter id of friends: "))
            t = Process(target=get_poll, args=(api, user_id))
            t1 = Process(target=write_messages, args=(api, user_id))
            t.start()
            sleep(1.5)
            t1.start()
            t1.join()


if __name__ == '__main__':
    main()
