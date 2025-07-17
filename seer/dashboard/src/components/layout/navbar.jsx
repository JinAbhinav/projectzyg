import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Shield, AlertTriangle, Search, Bell, BarChart, Settings, Menu, X, Brain, BrainCircuit, GitFork } from 'lucide-react';
import { Button } from '../ui/button';

const NavItem = ({ href, icon: Icon, children, isActive }) => {
  return (
    <Link href={href} passHref legacyBehavior>
      <Button
        variant="ghost"
        className={`w-full justify-start ${
          isActive ? 'bg-accent text-accent-foreground' : ''
        }`}
      >
        <Icon className="mr-2 h-5 w-5" />
        <span>{children}</span>
      </Button>
    </Link>
  );
};

export function Navbar() {
  const router = useRouter();
  const [isOpen, setIsOpen] = React.useState(false);

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: BarChart },
    { href: '/crawl', label: 'Crawler', icon: Search },
    { href: '/threats', label: 'Threats', icon: AlertTriangle },
    { href: '/parser', label: 'NLP/LLM Parser', icon: Brain },
    { href: '/alerts', label: 'Alerts', icon: Bell },
    { href: '/ai-analyzer', label: 'SEER AI', icon: BrainCircuit },
    { href: '/graph-explorer', label: 'Threat Map', icon: GitFork },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="md:hidden flex items-center justify-between p-4 border-b">
        <div className="flex items-center">
          <Shield className="h-6 w-6 text-primary mr-2" />
          <span className="font-bold text-xl">SEER</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle Menu"
        >
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>
      </div>

      {/* Sidebar for larger screens, overlay for mobile */}
      <div
        className={`fixed inset-0 z-50 transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 transition-transform duration-300 ease-in-out md:static md:z-auto md:w-64 bg-background border-r`}
      >
        <div className="p-6 md:block hidden">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="font-bold text-2xl">SEER</span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Cyber Threat Early Warning
          </p>
        </div>

        <div className="space-y-1 p-4">
          {navItems.map((item) => (
            <NavItem
              key={item.href}
              href={item.href}
              icon={item.icon}
              isActive={router.pathname === item.href}
            >
              {item.label}
            </NavItem>
          ))}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="p-4 rounded-lg bg-muted">
            <h4 className="text-sm font-medium mb-2">System Status</h4>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 rounded-full bg-green-500"></div>
              <span className="text-sm">All systems operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile menu */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
} 