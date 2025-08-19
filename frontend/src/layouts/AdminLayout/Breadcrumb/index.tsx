/* @ts-nocheck */
import React, { useState, useEffect, useMemo } from 'react';
// Replaced ListGroup shim with plain ul/li
import { Link, useLocation } from 'react-router-dom';

import navigation from '../../../menu-items';
import studentMenuItems from '../../../menu-items-student';
import teacherMenuItems from '../../../menu-items-teacher';
import adminMenuItems from '../../../menu-items-admin';
import { useAuth } from '../../../contexts/AuthContext';
import { BASE_TITLE } from '../../../config/constant';

const Breadcrumb = () => {
  const location = useLocation();
  const { user } = useAuth();

  // Seleziona il menu corretto basato sul ruolo dell'utente
  const selectedNavigation = useMemo(() => {
    if (!user?.role) return navigation;

    switch (user.role) {
      case 'student':
      case 'user':
        return studentMenuItems;
      case 'teacher':
        return teacherMenuItems;
      case 'admin':
      case 'staff':
        return adminMenuItems;
      default:
        return navigation;
    }
  }, [user?.role]);

  const [main, setMain] = useState([]);
  const [item, setItem] = useState([]);

  useEffect(() => {
    selectedNavigation.items.map((item, index) => {
      if (item.type && item.type === 'group') {
        getCollapse(item, index);
      }
      return false;
    });
  });

  const getCollapse = (item, index) => {
    if (item.children) {
      item.children.filter((collapse) => {
        if (collapse.type && collapse.type === 'collapse') {
          getCollapse(collapse, index);
        } else if (collapse.type && collapse.type === 'item') {
          if (location.pathname === collapse.url) {
            setMain(item);
            setItem(collapse);
          }
        }
        return false;
      });
    }
  };

  let mainContent, itemContent;
  let breadcrumbContent = '';
  let title = '';

  if (main && main.type === 'collapse') {
    mainContent = (
      <li className="breadcrumb-item">
        <Link to="#">{main.title}</Link>
      </li>
    );
  }

  if (item && item.type === 'item') {
    title = item.title;
    itemContent = (
      <li className="breadcrumb-item">
        <Link to="#">{title}</Link>
      </li>
    );

    if (item.breadcrumbs !== false) {
      breadcrumbContent = (
        <div className="page-header">
          <div className="page-block">
            <div className="row align-items-center">
              <div className="col-md-12">
                <div className="page-header-title">
                  <h5 className="m-b-10">{title}</h5>
                </div>
                <ul className="breadcrumb">
                  <li className="breadcrumb-item">
                    <Link to="/">
                      <i className="feather icon-home" />
                    </Link>
                  </li>
                  {mainContent}
                  {itemContent}
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    document.title = title + BASE_TITLE;
  }

  return <React.Fragment>{breadcrumbContent}</React.Fragment>;
};

export default Breadcrumb;
