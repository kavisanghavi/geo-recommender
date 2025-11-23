import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { MapPin, Users, UserPlus, Home, Building2 } from 'lucide-react';
import clsx from 'clsx';

export default function Layout() {
    const location = useLocation();

    const navItems = [
        { icon: Home, label: 'Feed', path: '/' },
        { icon: UserPlus, label: 'Create User', path: '/create' },
        { icon: Users, label: 'Profiles', path: '/profiles' },
        { icon: Building2, label: 'Businesses', path: '/businesses' },
    ];

    return (
        <div className="flex h-screen w-screen bg-gray-50 text-gray-900 font-sans">
            {/* Sidebar */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col shadow-sm z-20">
                <div className="p-6 border-b border-gray-100">
                    <h1 className="text-xl font-bold flex items-center gap-2 text-indigo-600">
                        <MapPin className="w-6 h-6" />
                        GeoSocial
                    </h1>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={clsx(
                                    'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200',
                                    isActive
                                        ? 'bg-indigo-50 text-indigo-600 font-medium shadow-sm'
                                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                                )}
                            >
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-gray-100">
                    <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
                        <p className="font-bold mb-1">Simulation Mode</p>
                        <p>Create users, add friends, and mark places to see the engine work.</p>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden relative">
                <Outlet />
            </div>
        </div>
    );
}
