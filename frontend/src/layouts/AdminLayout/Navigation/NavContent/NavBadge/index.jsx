import PropTypes from 'prop-types';
import React from 'react';

const NavBadge = ({ items }) => {
  let navBadges = false;
  if (items.inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground) {
    const badgeClass = ['label', 'pcoded-inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground', items.inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground.type];

    navBadges = <span className={badgeClass.join(' ')}>{items.inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground.title}</span>;
  }

  return <React.Fragment>{navBadges}</React.Fragment>;
};

NavBadge.propTypes = {
  items: PropTypes.object,
  inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground: PropTypes.string,
  type: PropTypes.string,
  title: PropTypes.string
};

export default NavBadge;
