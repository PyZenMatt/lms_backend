import { dashboardScrollActions } from './utils/scrollHelpers';

const teacherMenuItems = {
  items: [
    {
      id: 'teacher-dashboard',
      title: 'Dashboard Docente',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'dashboard-overview',
          title: 'Overview',
          type: 'item',
          icon: 'feather icon-home',
          url: '/dashboard/teacher',
          action: dashboardScrollActions.teacher.overview
        },
        {
          id: 'teo-coins-balance',
          title: 'Saldo TeoCoin',
          type: 'item',
          icon: 'feather icon-dollar-sign',
          action: dashboardScrollActions.teacher.balance
        },
        {
          id: 'sales-statistics',
          title: 'Statistiche Vendite',
          type: 'item',
          icon: 'feather icon-trending-up',
          action: dashboardScrollActions.teacher.sales
        },
        {
          id: 'my-courses-teacher',
          title: 'I Miei Corsi',
          type: 'item',
          icon: 'feather icon-book',
          action: dashboardScrollActions.teacher.courses
        },
        {
          id: 'transactions-teacher',
          title: 'Transazioni',
          type: 'item',
          icon: 'feather icon-credit-card',
          action: dashboardScrollActions.teacher.transactions
        },
        {
          id: 'lessons-management',
          title: 'Gestione Lezioni',
          type: 'item',
          icon: 'feather icon-play-circle',
          action: dashboardScrollActions.teacher.lessons
        }
      ]
    },
    {
      id: 'course-management',
      title: 'Gestione Corsi',
      type: 'group',
      icon: 'icon-ui',
      children: [
        {
          id: 'create-course',
          title: 'Crea Nuovo Corso',
          type: 'item',
          icon: 'feather icon-plus-circle',
          badge: {
            title: 'CREATE',
            type: 'label-primary'
          },
          action: () => {
            const createButton = document.querySelector('button:contains("+ Crea nuovo corso")') ||
                               [...document.querySelectorAll('button')].find(btn => 
                                 btn.textContent.includes('Crea nuovo corso')
                               );
            if (createButton) {
              createButton.click();
            } else {
              alert('Pulsante di creazione corso non trovato sulla pagina');
            }
          }
        },
        {
          id: 'browse-courses',
          title: 'Esplora Corsi d\'Arte',
          type: 'item',
          icon: 'feather icon-palette',
          url: '/corsi'
        },
        {
          id: 'course-analytics',
          title: 'Analytics Corsi',
          type: 'item',
          icon: 'feather icon-bar-chart-2',
          url: '/teacher/analytics'
        },
        {
          id: 'student-submissions',
          title: 'Sottomissioni Studenti',
          type: 'item',
          icon: 'feather icon-file-text',
          url: '/teacher/submissions'
        },
        {
          id: 'peer-review-management',
          title: 'Gestione Peer Review',
          type: 'item',
          icon: 'feather icon-users',
          url: '/teacher/peer-reviews'
        }
      ]
    },
    {
      id: 'web3-tools',
      title: 'Strumenti Web3',
      type: 'group',
      icon: 'icon-charts',
      children: [
        {
          id: 'smart-contracts',
          title: 'Smart Contracts',
          type: 'item',
          icon: 'feather icon-shield',
          badge: {
            title: 'BETA',
            type: 'label-warning'
          },
          url: '/teacher/smart-contracts'
        },
        {
          id: 'nft-certificates',
          title: 'Certificati NFT',
          type: 'item',
          icon: 'feather icon-award',
          url: '/teacher/nft-certificates'
        },
        {
          id: 'teocoin-rewards',
          title: 'Sistema Ricompense',
          type: 'item',
          icon: 'feather icon-gift',
          url: '/teacher/rewards'
        }
      ]
    },
    {
      id: 'teacher-profile',
      title: 'Profilo Docente',
      type: 'group',
      icon: 'icon-pages',
      children: [
        {
          id: 'my-profile-teacher',
          title: 'Il Mio Profilo',
          type: 'item',
          icon: 'feather icon-user',
          url: '/profile'
        },
        {
          id: 'notifications-teacher',
          title: 'Notifiche',
          type: 'item',
          icon: 'feather icon-bell',
          url: '/profile/notifications'
        },
        {
          id: 'teacher-settings',
          title: 'Impostazioni',
          type: 'item',
          icon: 'feather icon-settings',
          url: '/profile/settings'
        },
        {
          id: 'teaching-stats',
          title: 'Progressi & Statistiche',
          type: 'item',
          icon: 'feather icon-activity',
          url: '/profile/progress'
        },
        {
          id: 'logout-teacher',
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

export default teacherMenuItems;
