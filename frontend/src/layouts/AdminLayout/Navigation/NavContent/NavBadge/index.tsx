/* @ts-nocheck */
import PropTypes from 'prop-types';
import React from 'react';

const NavBadge = ({ items }) => {
  if (!items?.badge) return null;
  const { type, title } = items.badge;
  const badgeClass = ['label', 'pcoded-badge', type];
  return <span className={badgeClass.filter(Boolean).join(' ')}>{title}</span>;
};

NavBadge.propTypes = {
  items: PropTypes.shape({
    badge: PropTypes.shape({
      type: PropTypes.string,
      title: PropTypes.string
    })
  })
};

export default NavBadge;
