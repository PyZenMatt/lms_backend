/* @ts-nocheck */
import React, { useState } from 'react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui';
import { Link } from 'react-router-dom';

import ChatList from './ChatList';
import { useAuth } from '../../../../contexts/AuthContext';
import ThemeToggle from '../../../../components/ui/ui-legacy/ThemeToggle';
import UnifiedTeacherNotifications from '../../../../components/teacher/UnifiedTeacherNotifications.jsx';

import avatar1 from '../../../../assets/images/user/avatar-1.jpg';
// avatars used in menu header

const NavRight = () => {
  const [listOpen, setListOpen] = useState(false);
  const { logout } = useAuth();

  return (
    <React.Fragment>
  <ul className="navbar-nav ml-auto flex items-center gap-2" id="navbar-right">
        {/* Removed duplicate Teacher TeoCoin navbar widget to avoid double processing; use sidebar dashboard instead */}

        {/* Theme Toggle */}
        <li>
          <ThemeToggle size="sm" />
        </li>

        {/* Notifications dropdown with Accept/Decline actions for teachers */}
        <li>
          <UnifiedTeacherNotifications />
        </li>

        <li>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button aria-label="User menu" className="inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-accent focus:outline-none focus:ring">
                <i className="icon feather icon-settings" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="flex items-center gap-3 p-3 border-b">
                <img src={avatar1} className="h-10 w-10 rounded-full object-cover" alt="User" />
                <div className="flex flex-col text-sm">
                  <span className="font-medium">John Doe</span>
                  <button
                    className="text-xs text-muted-foreground hover:text-destructive"
                    onClick={(e) => {
                      e.preventDefault();
                      logout();
                    }}
                  >Logout</button>
                </div>
              </div>
              <DropdownMenuItem asChild>
                <Link to="#" className="flex items-center gap-2">
                  <i className="feather icon-settings" />
                  <span>Settings</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="#" className="flex items-center gap-2">
                  <i className="feather icon-user" />
                  <span>Profile</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="#" className="flex items-center gap-2">
                  <i className="feather icon-mail" />
                  <span>My Messages</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="#" className="flex items-center gap-2">
                  <i className="feather icon-lock" />
                  <span>Lock Screen</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </li>
      </ul>
      <ChatList listOpen={listOpen} closed={() => setListOpen(false)} />
    </React.Fragment>
  );
};

export default NavRight;
