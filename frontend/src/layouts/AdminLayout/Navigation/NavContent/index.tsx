/* @ts-nocheck */
import PropTypes from 'prop-types';
import React from 'react';
// Replaced ListGroup shim with plain ul/li
import PerfectScrollbar from 'react-perfect-scrollbar';

import NavGroup from './NavGroup';
import NavCard from './NavCard';

const NavContent = ({ navigation }) => {
  const navItems = navigation.map((item) => {
    switch (item.type) {
      case 'group':
        return <NavGroup key={'nav-group-' + item.id} group={item} />;
      default:
        return false;
    }
  });

  let mainContent = '';

  mainContent = (
    <div className="navbar-content datta-scroll">
      <PerfectScrollbar>
        <ul className="nav pcoded-inner-navbar" id="nav-ps-next">
          {navItems}
        </ul>
        <NavCard />
      </PerfectScrollbar>
    </div>
  );

  return <React.Fragment>{mainContent}</React.Fragment>;
};

NavContent.propTypes = {
  navigation: PropTypes.array
};

export default NavContent;
