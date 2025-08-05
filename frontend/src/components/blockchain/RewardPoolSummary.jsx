import React from 'react';
import { Card, Row, Col, Badge } from 'react-bootstrap';
import './RewardPoolSummary.scss';

/**
 * Widget to display current reward pool balances and status
 */
const RewardPoolSummary = ({ poolInfo }) => {
  if (!poolInfo) {
    return null;
  }

  const {
    teo_balance,
    matic_balance,
    address,
    warning_threshold,
    critical_threshold,
    status
  } = poolInfo;




// RewardPoolSummary.jsx - componente obsoleto

const RewardPoolSummary = () => null;

export default RewardPoolSummary;
