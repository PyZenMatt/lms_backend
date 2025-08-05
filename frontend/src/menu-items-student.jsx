import { dashboardScrollActions } from './utils/scrollHelpers';

const studentMenuItems = {
  items: [
    {
      id: 'dashboard-navigation',
      title: 'Dashboard',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'dashboard-overview',
          title: 'Overview',
          type: 'item',
          icon: 'feather icon-home',
          url: '/dashboard/student',
          action: dashboardScrollActions.student.overview
        },
        {
          id: 'teo-coins',
          title: 'Saldo TeoCoin',
          type: 'item',
          icon: 'feather icon-dollar-sign',
          action: dashboardScrollActions.student.balance
        },
        {
          id: 'my-courses',
          title: 'I Miei Corsi',
          type: 'item',
          icon: 'feather icon-book-open',
          action: dashboardScrollActions.student.courses
        },
        {
          id: 'transactions',
          title: 'Transazioni',
          type: 'item',
          icon: 'feather icon-credit-card',
          action: dashboardScrollActions.student.transactions
        },
        {
          id: 'my-submissions',
          title: 'I Miei Esercizi',
          type: 'item',
          icon: 'feather icon-file-text',
          action: dashboardScrollActions.student.exercises
        }
      ]
    },
    {
      id: 'student-actions',
      title: 'Azioni Studente',
      type: 'group',
      icon: 'icon-ui',
      children: [
        {
          id: 'browse-courses',
          title: 'Esplora Corsi d\'Arte',
          type: 'item',
          icon: 'feather icon-palette',
          url: '/corsi'
        },
        {
          id: 'peer-reviews',
          title: 'Peer Review',
          type: 'item',
          icon: 'feather icon-users',
          url: '/peer-review'
        },
        {
          id: 'web3-wallet',
          title: 'Wallet Web3',
          type: 'item',
          icon: 'feather icon-shield',
          badge: {
            title: 'NEW',
            type: 'label-success'
          },
          action: () => {
            // Apri modale wallet o naviga a pagina wallet
            alert('Funzionalità Wallet Web3 in arrivo!');
          }
        }
      ]
    },
    {
      id: 'student-profile',
      title: 'Profilo',
      type: 'group',
      icon: 'icon-pages',
      children: [
        {
          id: 'my-profile',
          title: 'Il Mio Profilo',
          type: 'item',
          icon: 'feather icon-user',
          url: '/profile'
        },
        {
          id: 'notifications',
          title: 'Notifiche',
          type: 'item',
          icon: 'feather icon-bell',
          url: '/profile/notifications'
        },
        {
          id: 'profile-settings',
          title: 'Impostazioni',
          type: 'item',
          icon: 'feather icon-settings',
          url: '/profile/settings'
        },
        {
          id: 'theme-settings',
          title: 'Tema & Aspetto',
          type: 'item',
          icon: 'feather icon-moon',
          url: '/profile/settings/theme',
          badge: {
            title: 'New',
            type: 'label-info'
          }
        },
        {
          id: 'achievements',
          title: 'Progressi & Achievement',
          type: 'item',
          icon: 'feather icon-award',
          badge: {
            title: 'Web3',
            type: 'label-warning'
          },
          url: '/profile/progress'
        },
        {
          id: 'logout',
          title: 'Logout',
          type: 'item',
          icon: 'feather icon-log-out',
          classes: 'nav-item text-danger',
          action: () => {
            if (window.confirm('Sei sicuro di voler uscire?')) {
              localStorage.removeItem('token');
              window.location.href = '/auth/signin-1';
            }
          }
        }
      ]
    }
  ]
};

export default studentMenuItems;
