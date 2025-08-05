import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { fetchApprovalStats } from '../../services/api/admin';
import { fetchPendingCourses } from '../../services/api/admin';
import StatWidget from './StatWidget';

const ApprovalStats = React.memo(() => {
  const [stats, setStats] = useState({
    pendingTeachers: 0,
    pendingCourses: 0,
    totalPending: 0,
    lastWeekApprovals: 0,
    loading: true,
    error: null
  });

  const loadStats = useCallback(async () => {
    try {
      const [teachersRes, coursesRes] = await Promise.all([
        fetchPendingTeachers(),
        fetchPendingCourses()
      ]);
      
      const pendingTeachers = teachersRes.data.length;
      const pendingCourses = coursesRes.data.length;
      const totalPending = pendingTeachers + pendingCourses;
      
      // Mock data for last week approvals - in real implementation, 
      // this would come from an API endpoint
      const lastWeekApprovals = Math.floor(Math.random() * 20) + 5;
      
      setStats({
        pendingTeachers,
        pendingCourses,
        totalPending,
        lastWeekApprovals,
        loading: false,
        error: null
      });
    } catch (error) {
      setStats(prev => ({ 
        ...prev, 
        loading: false, 
        error: 'Errore nel caricamento delle statistiche' 
      }));
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const statsData = useMemo(() => [
    {
      title: "Teacher in Attesa",
      value: stats.pendingTeachers,
      icon: "users",
      color: "#ff9500",
      subtitle: "Richieste da processare",
      trend: stats.pendingTeachers > 0 ? 'up' : 'neutral',
      gradientFrom: "#ff9500",
      gradientTo: "#ff6b35"
    },
    {
      title: "Corsi in Attesa",
      value: stats.pendingCourses,
      icon: "book-open",
      color: "#00d4aa",
      subtitle: "In revisione",
      trend: stats.pendingCourses > 0 ? 'up' : 'neutral',
      gradientFrom: "#00d4aa",
      gradientTo: "#00a885"
    },
    {
      title: "Totale Pending",
      value: stats.totalPending,
      icon: "clock",
      color: "#6c63ff",
      subtitle: "Elementi da approvare",
      trend: stats.totalPending > 5 ? 'up' : stats.totalPending > 0 ? 'neutral' : 'down',
      gradientFrom: "#6c63ff",
      gradientTo: "#5a54d4"
    },
    {
      title: "Approvazioni Settimana",
      value: stats.lastWeekApprovals,
      icon: "check-circle",
      color: "#28a745",
      subtitle: "Elementi processati",
      trend: "up",
      changeValue: `+${stats.lastWeekApprovals}`,
      gradientFrom: "#28a745",
      gradientTo: "#20c997"
    }
  ], [stats]);

  if (stats.loading) {
    return (
      <div className="row g-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="col-xl-3 col-lg-6 col-md-6 col-sm-6">
            <div className="card">
              <div className="card-body text-center py-4">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (stats.error) {
    return (
      <div className="alert alert-danger">
        <i className="feather icon-alert-circle me-2"></i>
        {stats.error}
      </div>
    );
  }

  return (
    <div className="row g-3">
      {statsData.map((statData, index) => (
        <div key={index} className="col-xl-3 col-lg-6 col-md-6 col-sm-6">
          <StatWidget
            {...statData}
          />
        </div>
      ))}
    </div>
  );
});

ApprovalStats.displayName = 'ApprovalStats';

export default ApprovalStats;
