import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ListGroup, Dropdown } from 'react-bootstrap';
import { Link } from 'react-router-dom';

import ChatList from './ChatList';
import { useAuth } from '../../../../contexts/AuthContext';
import ThemeToggle from '../../../../components/ui/ThemeToggle';

import avatar1 from '../../../../assets/images/user/avatar-1.jpg';
// avatars used in menu header

const NavRight = () => {
  const [listOpen, setListOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <React.Fragment>
      <ListGroup as="ul" bsPrefix=" " className="navbar-nav ml-auto" id="navbar-right">
        {/* Removed duplicate Teacher TeoCoin navbar widget to avoid double processing; use sidebar dashboard instead */}
        
        {/* Theme Toggle */}
        <ListGroup.Item as="li" bsPrefix=" ">
          <ThemeToggle size="sm" />
        </ListGroup.Item>
        
        <ListGroup.Item as="li" bsPrefix=" ">
          <button type="button" className="nav-link btn btn-link" onClick={() => navigate('/profile/notifications')} style={{ padding: 0 }}>
            <span className="pcoded-micon">
              <i className="feather icon-bell"></i>
            </span>
            <span className="pcoded-mtext">Notifiche</span>
          </button>
        </ListGroup.Item>
        
        <ListGroup.Item as="li" bsPrefix=" ">
          <Dropdown>
            <Dropdown.Toggle as={Link} variant="link" to="#" id="dropdown-basic">
              <i className="icon feather icon-settings" />
            </Dropdown.Toggle>
            <Dropdown.Menu align="end" className="profile-notification">
              <div className="pro-head">
                <img src={avatar1} className="img-radius" alt="User Profile" />
                <span>John Doe</span>
                <Link
                  to="#"
                  className="dud-logout"
                  title="Logout"
                  onClick={(e) => {
                    e.preventDefault();
                    logout();
                  }}
                >
                  <i className="feather icon-log-out" />
                </Link>
              </div>
              <ListGroup as="ul" bsPrefix=" " variant="flush" className="pro-body">
                <ListGroup.Item as="li" bsPrefix=" ">
                  <Link to="#" className="dropdown-item">
                    <i className="feather icon-settings" /> Settings
                  </Link>
                </ListGroup.Item>
                <ListGroup.Item as="li" bsPrefix=" ">
                  <Link to="#" className="dropdown-item">
                    <i className="feather icon-user" /> Profile
                  </Link>
                </ListGroup.Item>
                <ListGroup.Item as="li" bsPrefix=" ">
                  <Link to="#" className="dropdown-item">
                    <i className="feather icon-mail" /> My Messages
                  </Link>
                </ListGroup.Item>
                <ListGroup.Item as="li" bsPrefix=" ">
                  <Link to="#" className="dropdown-item">
                    <i className="feather icon-lock" /> Lock Screen
                  </Link>
                </ListGroup.Item>
              </ListGroup>
            </Dropdown.Menu>
          </Dropdown>
        </ListGroup.Item>
      </ListGroup>
      <ChatList listOpen={listOpen} closed={() => setListOpen(false)} />
    </React.Fragment>
  );
};

export default NavRight;
