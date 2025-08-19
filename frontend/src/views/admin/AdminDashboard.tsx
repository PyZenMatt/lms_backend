/* @ts-nocheck */
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
// Layout refactor: removed Row/Col (bootstrap) -> Tailwind grid
import RoleGuard from '../../components/guards/RoleGuard';
import PendingTeachersCard from '../../components/cards/PendingTeachersCard';
import PendingCoursesCard from '../../components/cards/PendingCoursesCard';
import AdminTeoCoinDashboard from '../../components/blockchain/DBAdminTeoCoinDashboard';
import TeoCoinWithdrawal from '../../components/TeoCoinWithdrawal';

const AdminDashboard = () => {
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);

  return (
    <RoleGuard allowedRoles={['admin']}>
      <>
        <Helmet>
          <title>SchoolPlatform Admin Dashboard</title>
        </Helmet>
        <div className="grid grid-cols-12 gap-3 mb-4">
          <div className="col-span-12 mb-4">
            <PendingTeachersCard />
          </div>
          <div className="col-span-12 mb-4">
            <PendingCoursesCard />
          </div>
          <div className="col-span-12 mb-4">
            <AdminTeoCoinDashboard onWithdrawalClick={() => setWithdrawalOpen(true)} />
          </div>
        </div>
        {/* TeoCoin Withdrawal Modal */}
        <TeoCoinWithdrawal
          open={withdrawalOpen}
          onClose={() => setWithdrawalOpen(false)}
          userBalance={0} // Admin balance will be fetched by the component itself
        />
      </>
    </RoleGuard>
  );
};

// (rimosso export default duplicato)
export default AdminDashboard;
