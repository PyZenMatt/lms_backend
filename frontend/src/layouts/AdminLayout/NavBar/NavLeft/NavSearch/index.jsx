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
        <div className="input-group">
          <input type="text" id="m-search" className="form-control" placeholder="Search . . ." style={{ width: searchString }} />
          <Link to="#" className="input-group-append search-close" onClick={searchOffHandler}>
            <i className="feather icon-x input-group-text" />
          </Link>
          <span
            onKeyDown={searchOnHandler}
            role="button"
            tabIndex="0"
            className="input-group-append search-inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground bg-primary text-primary-foreground"
            onClick={searchOnHandler}
            style={{ borderRadius: '50%', marginLeft: 5 }}
          >
            <i className="feather icon-search input-group-text" />
          </span>
        </div>
      </div>
    </React.Fragment>
  );
};

NavSearch.propTypes = {
  windowWidth: PropTypes.number
};

export default NavSearch;
