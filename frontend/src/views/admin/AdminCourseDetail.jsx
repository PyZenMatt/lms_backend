import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const AdminCourseDetail = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourse = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const res = await fetch(`/api/v1/courses/${courseId}/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setCourse(data);
    };
    const fetchLessons = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const res = await fetch(`/api/v1/courses/${courseId}/lessons/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setLessons(Array.isArray(data) ? data : []);
    };
    fetchCourse();
    fetchLessons();
    setLoading(false);
  }, [courseId]);

  if (loading) return <div>Caricamento...</div>;
  if (!course) return <div>Corso non trovato.</div>;

  return (
    <div className="container mt-4">
      <h2>{course.title}</h2>
      <p>{course.description}</p>
      <p><strong>Docente:</strong> {course.teacher?.username || '-'}</p>
      <h4>Lezioni</h4>
      <ul>
        {lessons.map(lesson => (
          <li key={lesson.id}>
            <Link to={`/admin/lezioni/${lesson.id}`}>
              {lesson.order ? `${lesson.order}. ` : ''}{lesson.title}
            </Link>
            {lesson.duration ? ` (${lesson.duration} min)` : ''}
          </li>
        ))}
      </ul>
      <Link to="/dashboard/admin" className="btn btn-secondary mt-3">
        Torna alla dashboard admin
      </Link>
    </div>
  );
};

export default AdminCourseDetail;
