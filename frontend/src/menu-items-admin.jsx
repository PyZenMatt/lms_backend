import { dashboardScrollActions } from './utils/scrollHelpers';

const adminMenuItems = {
  items: [
    {
      id: 'admin-dashboard',
      title: 'Dashboard Admin',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'admin-overview',
          title: 'Overview',
          type: 'item',
          icon: 'feather icon-home',
          url: '/dashboard/admin',
          action: dashboardScrollActions.admin.overview
        },
        {
          id: 'teocoin-balance-admin',
          title: 'Saldo TeoCoin',
          type: 'item',
          icon: 'feather icon-dollar-sign',
          action: dashboardScrollActions.admin.balance
        },
        {
          id: 'pending-teachers',
          title: 'Docenti in Attesa',
          type: 'item',
          icon: 'feather icon-user-check',
          badge: {
            title: 'PENDING',
            type: 'label-warning'
          },
          action: dashboardScrollActions.admin.pendingTeachers
        },
        {
          id: 'pending-courses',
          title: 'Corsi in Attesa',
          type: 'item',
          icon: 'feather icon-book',
          badge: {
            title: 'REVIEW',
            type: 'label-info'
          },
          action: dashboardScrollActions.admin.pendingCourses
        },
        {
          id: 'course-evaluation',
          title: 'Valutazione Corsi',
          type: 'item',
          icon: 'feather icon-check-circle',
          action: dashboardScrollActions.admin.pendingCourses
        }
      ]
    },
    {
      id: 'user-management',
      title: 'Gestione Utenti',
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
          id: 'all-users',
          title: 'Tutti gli Utenti',
          type: 'item',
          icon: 'feather icon-users',
          url: '/admin/users'
        },
        {
          id: 'teacher-approvals',
          title: 'Approvazioni Docenti',
          type: 'item',
          icon: 'feather icon-user-plus',
          url: '/admin/teacher-approvals'
        },
        {
          id: 'student-management',
          title: 'Gestione Studenti',
          type: 'item',
          icon: 'feather icon-user',
          url: '/admin/students'
        },
        {
          id: 'user-roles',
          title: 'Ruoli e Permessi',
          type: 'item',
          icon: 'feather icon-shield',
          url: '/admin/roles'
        }
      ]
    },
    {
      id: 'content-management',
      title: 'Gestione Contenuti',
      type: 'group',
      icon: 'icon-charts',
      children: [
        {
          id: 'course-approvals',
          title: 'Approvazioni Corsi',
          type: 'item',
          icon: 'feather icon-check-square',
          url: '/admin/course-approvals'
        },
        {
          id: 'content-moderation',
          title: 'Moderazione Contenuti',
          type: 'item',
          icon: 'feather icon-eye',
          url: '/admin/moderation'
        },
        {
          id: 'categories',
          title: 'Categorie Corsi',
          type: 'item',
          icon: 'feather icon-tag',
          url: '/admin/categories'
        },
        {
          id: 'reports',
          title: 'Report e Analytics',
          type: 'item',
          icon: 'feather icon-bar-chart',
          url: '/admin/reports'
        }
      ]
    },
    {
      id: 'web3-admin',
      title: 'Amministrazione Web3',
      type: 'group',
      icon: 'icon-charts',
      children: [
        {
          id: 'teocoin-management',
          title: 'Gestione TeoCoin',
          type: 'item',
          icon: 'feather icon-dollar-sign',
          badge: {
            title: 'CRYPTO',
            type: 'label-success'
          },
          url: '/admin/teocoin'
        },
        {
          id: 'smart-contract-admin',
          title: 'Smart Contract Admin',
          type: 'item',
          icon: 'feather icon-shield',
          url: '/admin/smart-contracts'
        },
        {
          id: 'blockchain-stats',
          title: 'Statistiche Blockchain',
          type: 'item',
          icon: 'feather icon-activity',
          url: '/admin/blockchain-stats'
        },
        {
          id: 'nft-admin',
          title: 'Gestione NFT',
          type: 'item',
          icon: 'feather icon-award',
          url: '/admin/nft'
        }
      ]
    },
    {
      id: 'admin-profile',
      title: 'Profilo Admin',
      type: 'group',
      icon: 'icon-pages',
      children: [
        {
          id: 'my-profile-admin',
          title: 'Il Mio Profilo',
          type: 'item',
          icon: 'feather icon-user',
          url: '/profile'
        },
        {
          id: 'notifications-admin',
          title: 'Notifiche',
          type: 'item',
          icon: 'feather icon-bell',
          url: '/profile/notifications'
        },
        {
          id: 'admin-settings',
          title: 'Impostazioni Profilo',
          type: 'item',
          icon: 'feather icon-settings',
          url: '/profile/settings'
        },
        {
          id: 'admin-stats',
          title: 'Statistiche Admin',
          type: 'item',
          icon: 'feather icon-activity',
          url: '/profile/progress'
        }
      ]
    },
    {
      id: 'system-settings',
      title: 'Sistema',
      type: 'group',
      icon: 'icon-pages',
      children: [
        {
          id: 'platform-settings',
          title: 'Impostazioni Piattaforma',
          type: 'item',
          icon: 'feather icon-settings',
          url: '/admin/settings'
        },
        {
          id: 'system-logs',
          title: 'Log di Sistema',
          type: 'item',
          icon: 'feather icon-file-text',
          url: '/admin/logs'
        },
        {
          id: 'backup-restore',
          title: 'Backup & Restore',
          type: 'item',
          icon: 'feather icon-database',
          url: '/admin/backup'
        },
        {
          id: 'admin-logout',
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

export default adminMenuItems;
