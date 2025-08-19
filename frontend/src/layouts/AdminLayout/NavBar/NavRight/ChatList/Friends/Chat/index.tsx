/* @ts-nocheck */
import PropTypes from 'prop-types';
import React from 'react';
import { Button, Card } from '@/components/ui';
import { Link } from 'react-router-dom';
import PerfectScrollbar from 'react-perfect-scrollbar';

import chatMsg from './chat';
import Messages from './Messages';

const Chat = ({ user, chatOpen, listOpen, closed }) => {
  let chatClass = ['header-chat'];
  if (chatOpen && listOpen) {
    chatClass = [...chatClass, 'open'];
  }

  let message = (
    <Card className="d-flex align-items-center shadow-none mb-0 p-0" style={{ flexDirection: 'row', backgroundColor: 'unset' }}>
      <Card.Body className="p-0 chat-menu-content">
        <div className="">
          <p className="chat-cont">CHAT NOT FOUND</p>
        </div>
      </Card.Body>
    </Card>
  );

  chatMsg.filter((chats) => {
    if (chats.friend_id === user.id) {
      message = chats.messages.map((msg, index) => {
        return <Messages key={index} message={msg} name={user.name} photo={chats.friend_photo} />;
      });
    }
    return false;
  });

  return (
    <React.Fragment>
      <div className={chatClass.join(' ')}>
        <div className="h-list-header">
          <h6>{user.name}</h6>
          <Link to="#" className="h-back-user-list" onClick={closed}>
            <i className="feather icon-chevron-left text-muted" />
          </Link>
        </div>
        <div className="h-list-body">
          <div className="main-chat-cont">
            <PerfectScrollbar>
              <div className="main-friend-chat">{message}</div>
            </PerfectScrollbar>
          </div>
        </div>
        <div className="h-list-footer">
          <div className="flex items-center gap-2 px-3 py-2">
            <button className="inline-flex items-center justify-center rounded-md h-9 px-3 py-2 text-sm bg-muted hover:bg-accent">
              <i className="feather icon-paperclip" />
            </button>
            <input type="text" name="h-chat-text" className="flex-1 h-9 border rounded-md px-3 text-sm" placeholder="Write here..." />
            <Button type="submit" className="inline-flex items-center justify-center rounded-md h-9 px-3 py-2 text-sm">
              <i className="feather icon-message-circle" />
            </Button>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
};

Chat.propTypes = {
  user: PropTypes.oneOfType([PropTypes.array, PropTypes.object]),
  chatOpen: PropTypes.bool,
  listOpen: PropTypes.bool,
  id: PropTypes.number,
  closed: PropTypes.func,
  name: PropTypes.string
};

export default Chat;
