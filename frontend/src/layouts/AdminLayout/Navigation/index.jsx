import React, { useContext, useMemo } from 'react';

import { ConfigContext } from '../../../contexts/ConfigContext';
import { useAuth } from '../../../contexts/AuthContext';
import useWindowSize from '../../../hooks/useWindowSize';

import NavLogo from './NavLogo';
import NavContent from './NavContent';
import navigation from '../../../menu-items';
import studentMenuItems from '../../../menu-items-student';
import teacherMenuItems from '../../../menu-items-teacher';
import adminMenuItems from '../../../menu-items-admin';

const Navigation = () => {
  const configContext = useContext(ConfigContext);
  const { collapseMenu } = configContext.state;
  const { user } = useAuth();
  const windowSize = useWindowSize();

  // Seleziona il menu corretto basato sul ruolo dell'utente
  const selectedNavigation = useMemo(() => {
    // Se non c'è un utente o non ha un ruolo, usa il menu di default
    if (!user || !user.role) {
      console.log('Nessun ruolo trovato, usando menu di default');
      return navigation;
    }
    
    const role = user.role.toLowerCase();
    console.log('Ruolo utente:', role);
    
    // Seleziona il menu in base al ruolo
    if (role === 'student' || role === 'user') {
      console.log('Usando menu studente');
      return studentMenuItems;
    } else if (role === 'teacher' || role === 'instructor') {
      console.log('Usando menu insegnante');
      return teacherMenuItems;
    } else if (role === 'admin' || role === 'staff') {
      console.log('Usando menu admin');
      return adminMenuItems;
    } else {
      console.log('Ruolo non riconosciuto, usando menu di default');
      return navigation;
    }
  }, [user]);

  let navClass = ['pcoded-navbar'];

  navClass = [...navClass];

  if (windowSize.width < 992 && collapseMenu) {
    navClass = [...navClass, 'mob-open'];
  } else if (collapseMenu) {
    navClass = [...navClass, 'navbar-collapsed'];
  }

  let navBarClass = ['navbar-wrapper'];

  let navContent = (
    <div className={navBarClass.join(' ')}>
      <NavLogo />
      <NavContent navigation={selectedNavigation.items} />
    </div>
  );
  if (windowSize.width < 992) {
    navContent = (
      <div className="navbar-wrapper">
        <NavLogo />
        <NavContent navigation={selectedNavigation.items} />
      </div>
    );
  }
  return (
    <React.Fragment>
      <nav className={navClass.join(' ')}>{navContent}</nav>
    </React.Fragment>
  );
};

export default Navigation;
