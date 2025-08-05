import React from 'react';

import { Row, Col } from 'react-bootstrap';
import PendingTeachersCard from '../../components/cards/PendingTeachersCard';
import PendingCoursesCard from '../../components/cards/PendingCoursesCard';
import AdminTeoCoinDashboard from '../../components/blockchain/DBAdminTeoCoinDashboard';
import '../dashboard/dashboard-styles.css';

const AdminDashboard = () => (
  <React.Fragment>
    <Row className="g-3 mb-4">
      <Col xs={12} className="mb-4">
        <PendingTeachersCard />
      </Col>
      <Col xs={12} className="mb-4">
        <PendingCoursesCard />
      </Col>
      <Col xs={12} className="mb-4">
        <AdminTeoCoinDashboard />
      </Col>
    </Row>
  </React.Fragment>
);

// (rimosso export default duplicato)
export default AdminDashboard;
