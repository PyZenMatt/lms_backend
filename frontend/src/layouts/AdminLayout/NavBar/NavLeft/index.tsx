/* @ts-nocheck */
import React from 'react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui';
import { Link } from 'react-router-dom';

import useWindowSize from '../../../../hooks/useWindowSize';
import NavSearch from './NavSearch';

const NavLeft = () => {
  const windowSize = useWindowSize();

  let navItemClass = ['nav-item'];
  if (windowSize.width <= 575) {
    navItemClass = [...navItemClass, 'd-none'];
  }

  return (
    <React.Fragment>
      <ul className="navbar-nav mr-auto flex items-center gap-2">
        <li className={navItemClass.join(' ')}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button id="dropdown-basic" className="px-3 py-2 text-sm rounded-md hover:bg-accent focus:outline-none focus:ring">
                Menu
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-44">
              <DropdownMenuItem asChild>
                <Link to="#">Action</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="#">Another action</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="#">Something else here</Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </li>
        <li className="nav-item">
          <NavSearch windowWidth={windowSize.width} />
        </li>
      </ul>
    </React.Fragment>
  );
};

export default NavLeft;
