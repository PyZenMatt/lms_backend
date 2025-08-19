/* @ts-nocheck */
import PropTypes from 'prop-types';
import React from 'react';
// Replaced ListGroup shim with plain li
import NavCollapse from '../NavCollapse';
import NavItem from '../NavItem';

const NavGroup = ({ layout, group }) => {
  let navItems = '';

  if (group.children) {
    const groups = group.children;
    navItems = Object.keys(groups).map((item) => {
      item = groups[item];
      switch (item.type) {
        case 'collapse':
          return <NavCollapse key={item.id} collapse={item} type="main" />;
        case 'item':
          return <NavItem layout={layout} key={item.id} item={item} />;
        default:
          return false;
      }
    });
  }

  return (
    <React.Fragment>
      <li key={group.id} className="nav-item pcoded-menu-caption">
        <label>{group.title}</label>
      </li>
      {navItems}
    </React.Fragment>
  );
};

NavGroup.propTypes = {
  layout: PropTypes.string,
  group: PropTypes.object,
  id: PropTypes.number,
  children: PropTypes.node,
  title: PropTypes.string
};

export default NavGroup;
