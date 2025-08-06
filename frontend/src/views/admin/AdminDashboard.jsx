import React, { useState } from 'react';

import { Row, Col } from 'react-bootstrap';
import PendingTeachersCard from '../../components/cards/PendingTeachersCard';
import PendingCoursesCard from '../../components/cards/PendingCoursesCard';
import AdminTeoCoinDashboard from '../../components/blockchain/DBAdminTeoCoinDashboard';
import TeoCoinWithdrawal from '../../components/TeoCoinWithdrawal';
import '../dashboard/dashboard-styles.css';

const AdminDashboard = () => {
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);

  return (
    <React.Fragment>
      <Row className="g-3 mb-4">
        <Col xs={12} className="mb-4">
          <PendingTeachersCard />
        </Col>
        <Col xs={12} className="mb-4">
          <PendingCoursesCard />
        </Col>
        <Col xs={12} className="mb-4">
          <AdminTeoCoinDashboard onWithdrawalClick={() => setWithdrawalOpen(true)} />
        </Col>
      </Row>
      
      {/* TeoCoin Withdrawal Modal */}
      <TeoCoinWithdrawal
        open={withdrawalOpen}
        onClose={() => setWithdrawalOpen(false)}
        userBalance={0} // Admin balance will be fetched by the component itself
      />
    </React.Fragment>
  );
};

// (rimosso export default duplicato)
export default AdminDashboard;
