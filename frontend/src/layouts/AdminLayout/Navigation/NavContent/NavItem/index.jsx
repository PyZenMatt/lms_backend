import PropTypes from 'prop-types';
import React, { useContext } from 'react';
import { ListGroup } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';

import NavIcon from '../NavIcon';
import NavBadge from '../NavBadge';

import { ConfigContext } from '../../../../../contexts/ConfigContext';
import * as actionType from '../../../../../store/actions';
import useWindowSize from '../../../../../hooks/useWindowSize';

const NavItem = ({ item }) => {
  const windowSize = useWindowSize();
  const configContext = useContext(ConfigContext);
  const { dispatch } = configContext;

  let itemTitle = item.title;
  if (item.icon) {
    itemTitle = <span className="pcoded-mtext">{item.title}</span>;
  }

  let itemTarget = '';
  if (item.target) {
    itemTarget = '_blank';
  }

  // Gestione della navigazione e delle azioni custom
  const handleClick = async (e) => {
    let handled = false;
    if (typeof item.action === 'function') {
      // Se l'azione è definita, eseguila (può essere async)
      e.preventDefault();
      handled = true;
      try {
        await item.action();
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error("Errore nell'azione custom del menu:", err);
      }
    }
    if (windowSize.width < 992) {
      dispatch({ type: actionType.COLLAPSE_MENU });
    }
    if (!handled) {
      // Navigazione normale
      // eslint-disable-next-line no-console
      console.log(`Navigando a: ${item.url}`);
    }
  };

  let subContent;
  if (item.external) {
    subContent = (
      <NavLink to={item.url} target={itemTarget} className="nav-link" activeClassName="active" onClick={handleClick}>
        <NavIcon items={item} />
        {itemTitle}
        <NavBadge items={item} />
      </NavLink>
    );
  } else {
    subContent = (
      <NavLink to={item.url || '#'} className="nav-link" activeClassName="active" target={itemTarget} onClick={handleClick} exact>
        <NavIcon items={item} />
        {itemTitle}
        <NavBadge items={item} />
      </NavLink>
    );
  }

  let mainContent = '';

  if (windowSize.width < 992) {
    mainContent = (
      <ListGroup.Item as="li" bsPrefix=" " className={item.classes}>
        {subContent}
      </ListGroup.Item>
    );
  } else {
    mainContent = (
      <ListGroup.Item as="li" bsPrefix=" " className={item.classes}>
        {subContent}
      </ListGroup.Item>
    );
  }

  return <React.Fragment>{mainContent}</React.Fragment>;
};

NavItem.propTypes = {
  item: PropTypes.object,
  title: PropTypes.string,
  icon: PropTypes.string,
  target: PropTypes.string,
  external: PropTypes.bool,
  url: PropTypes.string,
  classes: PropTypes.string
};

export default NavItem;
