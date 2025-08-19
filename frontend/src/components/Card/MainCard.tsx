import PropTypes from 'prop-types';
import React, { useState } from 'react';
import { Card, DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui';
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
      <div className={'px-2 py-1 ' + (optionClass || '')}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              aria-label="Card actions"
              className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent focus:outline-none focus:ring"
            >
              <i className="feather icon-more-horizontal" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem onClick={() => setFullCard(!fullCard)} className="flex items-center gap-2">
              <i className={fullCard ? 'feather icon-minimize' : 'feather icon-maximize'} />
              <span>{fullCard ? 'Restore' : 'Maximize'}</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setCollapseCard(!collapseCard)} className="flex items-center gap-2">
              <i className={collapseCard ? 'feather icon-plus' : 'feather icon-minus'} />
              <span>{collapseCard ? 'Expand' : 'Collapse'}</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={cardReloadHandler} className="flex items-center gap-2">
              <i className="feather icon-refresh-cw" />
              <span>Reload</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={cardRemoveHandler} className="flex items-center gap-2 text-destructive">
              <i className="feather icon-trash" />
              <span>Remove</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  }

  cardHeader = (
    <div className="flex items-center justify-between px-4 py-2 border-b">
      <h5 className="font-medium text-sm">{title}</h5>
      {cardHeaderRight}
    </div>
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
      {!collapseCard && <div className="p-4">{children}</div>}
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
