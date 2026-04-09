import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  SideNav,
  SideNavItems,
  SideNavLink,
  SideNavMenu,
  SideNavMenuItem,
  Content,
  SkipToContent,
} from '@carbon/react';
import {
  Activity,
  Dashboard,
  Report,
  UserMultiple,
  ChevronRight,
} from '@carbon/icons-react';
import { DEMO_WORKFLOWS } from '../../utils/api';

export default function AppShell({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <>
      <Header aria-label="DischargeIQ" className="app-header">
        <SkipToContent />
        <HeaderName
          href="/"
          prefix="IBM"
          onClick={(e) => {
            e.preventDefault();
            navigate('/');
          }}
        >
          DischargeIQ
        </HeaderName>
        <HeaderNavigation aria-label="Main navigation">
          <HeaderMenuItem
            href="/"
            isCurrentPage={location.pathname === '/'}
            onClick={(e) => {
              e.preventDefault();
              navigate('/');
            }}
          >
            Dashboard
          </HeaderMenuItem>
          <HeaderMenuItem
            href="/audit"
            isCurrentPage={location.pathname === '/audit'}
            onClick={(e) => {
              e.preventDefault();
              navigate('/audit');
            }}
          >
            Audit Log
          </HeaderMenuItem>
        </HeaderNavigation>
        <HeaderGlobalBar />
      </Header>

      <SideNav
        aria-label="Side navigation"
        isRail
        expanded={false}
      >
        <SideNavItems>
          <SideNavLink
            renderIcon={Dashboard}
            href="/"
            onClick={(e) => {
              e.preventDefault();
              navigate('/');
            }}
          >
            Dashboard
          </SideNavLink>
          <SideNavLink
            renderIcon={Report}
            href="/audit"
            onClick={(e) => {
              e.preventDefault();
              navigate('/audit');
            }}
          >
            Audit Log
          </SideNavLink>
          <SideNavMenu renderIcon={UserMultiple} title="Patients">
            {DEMO_WORKFLOWS.map((wf) => (
              <SideNavMenuItem
                key={wf.patient_id}
                href={`/patients/${wf.patient_id}`}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(`/patients/${wf.patient_id}`);
                }}
              >
                {wf.patient_name}
              </SideNavMenuItem>
            ))}
          </SideNavMenu>
        </SideNavItems>
      </SideNav>

      <Content>{children}</Content>
    </>
  );
}
