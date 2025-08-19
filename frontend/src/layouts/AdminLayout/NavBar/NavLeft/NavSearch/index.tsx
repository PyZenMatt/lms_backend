/* @ts-nocheck */
import PropTypes from 'prop-types';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const NavSearch = (props) => {
  const { windowWidth } = props;
  const [isOpen, setIsOpen] = useState(windowWidth < 600);
  const [searchString, setSearchString] = useState(windowWidth < 600 ? '100px' : '');

  const searchOnHandler = () => {
    if (windowWidth < 600) {
      document.querySelector('#navbar-right').classList.add('d-none');
    }
    setIsOpen(true);
    setSearchString('100px');
  };

  const searchOffHandler = () => {
    setIsOpen(false);
    setSearchString(0);
    setTimeout(() => {
      if (windowWidth < 600) {
        document.querySelector('#navbar-right').classList.remove('d-none');
      }
    }, 500);
  };

  let searchClass = ['main-search'];
  if (isOpen) {
    searchClass = [...searchClass, 'open'];
  }

  return (
    <React.Fragment>
      <div id="main-search" className={searchClass.join(' ')}>
        <div className="flex items-center gap-2">
          <input
            type="text"
            id="m-search"
            className="h-9 w-[var(--w,100px)] transition-all duration-200 border rounded-md px-3 text-sm bg-background text-foreground focus:outline-none focus:ring"
            placeholder="Search..."
            style={{ ['--w']: searchString }}
          />
          <Link to="#" className="text-muted-foreground hover:text-foreground" onClick={searchOffHandler}>
            <i className="feather icon-x" />
          </Link>
          <button
            onKeyDown={searchOnHandler}
            onClick={searchOnHandler}
            type="button"
            className="inline-flex items-center justify-center rounded-full h-9 w-9 text-sm font-medium bg-primary text-primary-foreground focus:outline-none focus:ring"
          >
            <i className="feather icon-search" />
          </button>
        </div>
      </div>
    </React.Fragment>
  );
};

NavSearch.propTypes = {
  windowWidth: PropTypes.number
};

export default NavSearch;
