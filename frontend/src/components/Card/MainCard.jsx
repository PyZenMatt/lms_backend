import PropTypes from 'prop-types';
import React, { useState } from 'react';
// TODO: Replace legacy-shims usage with native UI primitives (Dropdown, Card, Collapse) once equivalents exist.
import { Dropdown, Card, Collapse } from '@/components/ui/legacy-shims';
import { Link } from 'react-router-dom';

import useWindowSize from '../../hooks/useWindowSize';

const MainCard = (props) => {
  const { isOption, title, children, cardClass, optionClass } = props;

  const [fullCard, setFullCard] = useState(false);
  const [collapseCard, setCollapseCard] = useState(false);
  const [loadCard, setloadCard] = useState(false);
  const [cardRemove, setCardRemove] = useState(false);

  const windowSize = useWindowSize();

  const cardReloadHandler = () => {
    setloadCard(true);
    setInterval(() => {
      setloadCard(false);
    }, 3000);
  };

  const cardRemoveHandler = () => {
    setCardRemove(true);
  };

  let fullScreenStyle, loader, cardHeaderRight, cardHeader;
  let cardMarkup = '';
  let mainCardClass = [];

  if (isOption) {
    cardHeaderRight = (
      <div className={'px-4 py-2 border-b border-border-right ' + optionClass}>
        <Dropdown align="end" className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-group bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm-option">
          <Dropdown.Toggle id="dropdown-basic" className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-icon">
            <i className="feather icon-more-horizontal" />
          </Dropdown.Toggle>
          <Dropdown.Menu as="ul" className="list-unstyled bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm-option">
            <Dropdown.Item as="li" className="dropdown-item" onClick={() => setFullCard(!fullCard)}>
              <i className={fullCard ? 'feather icon-minimize' : 'feather icon-maximize'} />
              <Link to="#"> {fullCard ? 'Restore' : 'Maximize'} </Link>
            </Dropdown.Item>
            <Dropdown.Item as="li" className="dropdown-item" onClick={() => setCollapseCard(!collapseCard)}>
              <i className={collapseCard ? 'feather icon-plus' : 'feather icon-minus'} />
              <Link to="#"> {collapseCard ? 'Expand' : 'Collapse'} </Link>
            </Dropdown.Item>
            <Dropdown.Item as="li" className="dropdown-item" onClick={cardReloadHandler}>
              <i className="feather icon-refresh-cw" />
              <Link to="#"> Reload </Link>
            </Dropdown.Item>
            <Dropdown.Item as="li" className="dropdown-item" onClick={cardRemoveHandler}>
              <i className="feather icon-trash" />
              <Link to="#"> Remove </Link>
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </div>
    );
  }

  cardHeader = (
    <Card.Header>
      <Card.Title as="h5">{title}</Card.Title>
      {cardHeaderRight}
    </Card.Header>
  );

  if (fullCard) {
  mainCardClass = [...mainCardClass, 'full-bg-card text-card-foreground rounded-lg border border-border shadow-sm shadow-lg'];
    fullScreenStyle = { position: 'fixed', top: 0, left: 0, right: 0, width: windowSize.width, height: windowSize.height };
  }

  if (loadCard) {
  mainCardClass = [...mainCardClass, 'bg-card text-card-foreground rounded-lg border border-border shadow-sm-loading'];
    loader = (
  <div className="bg-card text-card-foreground rounded-lg border border-border shadow-sm-loader">
        <i className="pct-loader1 anim-rotate" />
      </div>
    );
  }

  if (cardRemove) {
    mainCardClass = [...mainCardClass, 'd-none'];
  }

  if (cardClass) {
    mainCardClass = [...mainCardClass, cardClass];
  }

  cardMarkup = (
    <Card className={mainCardClass.join(' ')} style={fullScreenStyle}>
      {cardHeader}
      <Collapse in={!collapseCard}>
        <div>
          <Card.Body>{children}</Card.Body>
        </div>
      </Collapse>
      {loader}
    </Card>
  );

  return <>{cardMarkup}</>;
};

MainCard.propTypes = {
  isOption: PropTypes.bool,
  title: PropTypes.string,
  children: PropTypes.node,
  cardClass: PropTypes.string,
  optionClass: PropTypes.string
};

export default MainCard;
