import React, { useState, useEffect } from 'react';
import { ProgressBar } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { fetchUserProgress, transformProgressData } from '../../services/api/profile';

const ProfileProgress = () => {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Load user progress data
  useEffect(() => {
    loadProgressData();
  }, []);

  const loadProgressData = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await fetchUserProgress();
      const transformedData = transformProgressData(response.data);
      setProgressData(transformedData);
    } catch (err) {
      console.error('Error loading progress data:', err);
      setError('Errore nel caricamento dei dati di progresso');
      // Fallback to mock data if API fails
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadMockData = () => {
    const mockData = {
      overall: {
        coursesCompleted: 12,
        coursesInProgress: 3,
        totalCourses: 25,
        teoCoinsEarned: 2450,
        hoursLearned: 127,
        averageScore: 87
      },
      categories: [
        {
          id: 'painting',
          name: 'Pittura',
          icon: 'image',
          progress: 75,
          coursesCompleted: 6,
          totalCourses: 8,
          color: '#ff6b6b'
        },
        {
          id: 'sculpture',
          name: 'Scultura',
          icon: 'box',
          progress: 40,
          coursesCompleted: 2,
          totalCourses: 5,
          color: '#4ecdc4'
        },
        {
          id: 'drawing',
          name: 'Disegno',
          icon: 'edit-3',
          progress: 90,
          coursesCompleted: 4,
          totalCourses: 4,
          color: '#45b7d1'
        },
        {
          id: 'digital',
          name: 'Arte Digitale',
          icon: 'monitor',
          progress: 25,
          coursesCompleted: 0,
          totalCourses: 8,
          color: '#f9ca24'
        }
      ],
      achievements: [
        {
          id: 1,
          title: 'Primo Passo',
          description: 'Completa il tuo primo corso',
          earned: true,
          earnedDate: '2024-01-15',
          icon: 'award',
          color: '#feca57'
        },
        {
          id: 2,
          title: 'Artista Dedito',
          description: 'Completa 5 corsi',
          earned: true,
          earnedDate: '2024-03-10',
          icon: 'star',
          color: '#ff6b6b'
        },
        {
          id: 3,
          title: 'Maestro della Pittura',
          description: 'Completa tutti i corsi di pittura',
          earned: false,
          progress: 75,
          icon: 'image',
          color: '#48dbfb'
        },
        {
          id: 4,
          title: 'Collezionista di TeoCoins',
          description: 'Accumula 1000 TeoCoins',
          earned: true,
          earnedDate: '2024-02-20',
          icon: 'dollar-sign',
          color: '#1dd1a1'
        },
        {
          id: 5,
          title: 'Studente Perfetto',
          description: 'Ottieni una media del 95%',
          earned: false,
          progress: 87,
          icon: 'target',
          color: '#fd79a8'
        }
      ],
      recentActivity: [
        {
          id: 1,
          type: 'course_completed',
          title: 'Corso completato: Acquerello Avanzato',
          date: '2024-05-28',
          score: 92,
          teoCoins: 150
        },
        {
          id: 2,
          type: 'achievement_earned',
          title: 'Risultato sbloccato: Artista Dedito',
          date: '2024-05-25'
        },
        {
          id: 3,
          type: 'course_started',
          title: 'Iniziato: Scultura Contemporanea',
          date: '2024-05-20'
        }
      ]
    };

    setProgressData(mockData);
  };

  const filteredCategories = progressData?.categories.filter(cat => {
    if (selectedCategory === 'all') return true;
    if (selectedCategory === 'completed') return cat.progress === 100;
    if (selectedCategory === 'in-progress') return cat.progress > 0 && cat.progress < 100;
    if (selectedCategory === 'not-started') return cat.progress === 0;
    return true;
  }) || [];

  if (loading) {
    return (
      <div className="enhanced-profile-container">
        <div className="enhanced-loading-overlay">
          <div className="enhanced-loading-spinner"></div>
          <p className="enhanced-loading-text">Caricamento progressi...</p>
        </div>
      </div>
    );
  }

  if (error && !progressData) {
    return (
      <div className="enhanced-profile-container">
        <div className="enhanced-error-container">
          <div className="enhanced-alert enhanced-alert-danger">
            <i className="feather icon-alert-circle"></i>
            <span>{error}</span>
          </div>
          <button 
            className="enhanced-btn enhanced-btn-primary"
            onClick={loadProgressData}
          >
            <i className="feather icon-refresh-cw"></i>
            <span>Riprova</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="enhanced-profile-container">
      {/* Floating Decorative Elements */}
      <div className="enhanced-floating-decoration enhanced-deco-1"></div>
      <div className="enhanced-floating-decoration enhanced-deco-2"></div>
      <div className="enhanced-floating-decoration enhanced-deco-3"></div>

      {/* Header */}
      <div className="enhanced-profile-hero">
        <div className="container">
          <div className="enhanced-profile-header">
            <div className="enhanced-progress-header">
              <h1 className="enhanced-profile-name">
                <i className="feather icon-trending-up"></i>
                I Tuoi Progressi
              </h1>
              <p className="enhanced-progress-subtitle">
                Traccia il tuo percorso artistico e celebra i tuoi successi
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Profile Navigation */}
      <div className="container">
        <div className="enhanced-profile-navigation">
          <Link to="/profile" className="enhanced-nav-item">
            <i className="feather icon-user"></i>
            <span>Profilo</span>
          </Link>
          <Link to="/profile/notifications" className="enhanced-nav-item">
            <i className="feather icon-bell"></i>
            <span>Notifiche</span>
          </Link>
          <Link to="/profile/settings" className="enhanced-nav-item">
            <i className="feather icon-settings"></i>
            <span>Impostazioni</span>
          </Link>
          <Link to="/profile/progress" className="enhanced-nav-item active">
            <i className="feather icon-award"></i>
            <span>Progressi</span>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="container">
        
        {/* Overall Stats */}
        <div className="enhanced-progress-overview">
          <div className="enhanced-stat-card enhanced-stat-primary">
            <div className="enhanced-stat-icon">
              <i className="feather icon-book-open"></i>
            </div>
            <div className="enhanced-stat-content">
              <div className="enhanced-stat-value">{progressData.overall.coursesCompleted}</div>
              <div className="enhanced-stat-label">Corsi Completati</div>
            </div>
          </div>

          <div className="enhanced-stat-card enhanced-stat-success">
            <div className="enhanced-stat-icon">
              <i className="feather icon-dollar-sign"></i>
            </div>
            <div className="enhanced-stat-content">
              <div className="enhanced-stat-value">{progressData.overall.teoCoinsEarned}</div>
              <div className="enhanced-stat-label">TeoCoins Guadagnati</div>
            </div>
          </div>

          <div className="enhanced-stat-card enhanced-stat-info">
            <div className="enhanced-stat-icon">
              <i className="feather icon-clock"></i>
            </div>
            <div className="enhanced-stat-content">
              <div className="enhanced-stat-value">{progressData.overall.hoursLearned}h</div>
              <div className="enhanced-stat-label">Ore di Studio</div>
            </div>
          </div>

          <div className="enhanced-stat-card enhanced-stat-warning">
            <div className="enhanced-stat-icon">
              <i className="feather icon-target"></i>
            </div>
            <div className="enhanced-stat-content">
              <div className="enhanced-stat-value">{progressData.overall.averageScore}%</div>
              <div className="enhanced-stat-label">Media Voti</div>
            </div>
          </div>
        </div>

        {/* Category Progress */}
        <div className="enhanced-progress-section">
          <div className="enhanced-section-header">
            <h3 className="enhanced-section-title">
              <i className="feather icon-layers"></i>
              <span>Progressi per Categoria</span>
            </h3>
            <div className="enhanced-progress-filters">
              <button 
                className={`enhanced-filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('all')}
              >
                Tutte
              </button>
              <button 
                className={`enhanced-filter-btn ${selectedCategory === 'completed' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('completed')}
              >
                Completate
              </button>
              <button 
                className={`enhanced-filter-btn ${selectedCategory === 'in-progress' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('in-progress')}
              >
                In Corso
              </button>
              <button 
                className={`enhanced-filter-btn ${selectedCategory === 'not-started' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('not-started')}
              >
                Da Iniziare
              </button>
            </div>
          </div>

          <div className="enhanced-category-grid">
            {filteredCategories.map(category => (
              <div key={category.id} className="enhanced-category-card">
                <div className="enhanced-category-header">
                  <div className="enhanced-category-icon" style={{backgroundColor: category.color}}>
                    <i className={`feather icon-${category.icon}`}></i>
                  </div>
                  <div className="enhanced-category-info">
                    <h4 className="enhanced-category-name">{category.name}</h4>
                    <p className="enhanced-category-stats">
                      {category.coursesCompleted}/{category.totalCourses} corsi
                    </p>
                  </div>
                  <div className="enhanced-category-percentage">
                    {category.progress}%
                  </div>
                </div>
                <div className="enhanced-category-progress">
                  <ProgressBar 
                    now={category.progress} 
                    className="enhanced-progress-bar"
                    style={{'--progress-color': category.color}}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Achievements Section */}
        <div className="enhanced-progress-section">
          <div className="enhanced-section-header">
            <h3 className="enhanced-section-title">
              <i className="feather icon-award"></i>
              <span>Risultati</span>
            </h3>
          </div>

          <div className="enhanced-achievements-grid">
            {progressData.achievements.map(achievement => (
              <div 
                key={achievement.id} 
                className={`enhanced-achievement-card ${achievement.earned ? 'earned' : 'locked'}`}
              >
                <div className="enhanced-achievement-icon" style={{backgroundColor: achievement.color}}>
                  <i className={`feather icon-${achievement.icon}`}></i>
                </div>
                <div className="enhanced-achievement-content">
                  <h4 className="enhanced-achievement-title">{achievement.title}</h4>
                  <p className="enhanced-achievement-description">{achievement.description}</p>
                  {achievement.earned ? (
                    <div className="enhanced-achievement-earned">
                      <i className="feather icon-check-circle"></i>
                      <span>Sbloccato il {new Date(achievement.earnedDate).toLocaleDateString('it-IT')}</span>
                    </div>
                  ) : (
                    <div className="enhanced-achievement-progress">
                      <div className="enhanced-achievement-progress-text">
                        Progresso: {achievement.progress || 0}%
                      </div>
                      <ProgressBar 
                        now={achievement.progress || 0} 
                        className="enhanced-progress-bar-small"
                      />
                    </div>
                  )}
                </div>
                {achievement.earned && (
                  <div className="enhanced-achievement-badge">
                    <i className="feather icon-star"></i>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="enhanced-progress-section">
          <div className="enhanced-section-header">
            <h3 className="enhanced-section-title">
              <i className="feather icon-activity"></i>
              <span>Attività Recente</span>
            </h3>
          </div>

          <div className="enhanced-activity-list">
            {progressData.recentActivity.map(activity => (
              <div key={activity.id} className="enhanced-activity-item">
                <div className={`enhanced-activity-icon ${activity.type}`}>
                  <i className={`feather icon-${
                    activity.type === 'course_completed' ? 'check-circle' :
                    activity.type === 'achievement_earned' ? 'award' :
                    'play-circle'
                  }`}></i>
                </div>
                <div className="enhanced-activity-content">
                  <h5 className="enhanced-activity-title">{activity.title}</h5>
                  <div className="enhanced-activity-meta">
                    <span className="enhanced-activity-date">
                      {new Date(activity.date).toLocaleDateString('it-IT')}
                    </span>
                    {activity.score && (
                      <span className="enhanced-activity-score">
                        Voto: {activity.score}%
                      </span>
                    )}
                    {activity.teoCoins && (
                      <span className="enhanced-activity-coins">
                        +{activity.teoCoins} TeoCoins
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileProgress;
