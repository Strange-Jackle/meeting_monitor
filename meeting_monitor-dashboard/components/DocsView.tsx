import React from 'react';
import { ArrowLeft, ChevronRight, Hash, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DocsView: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-white text-slate-900 font-sans">
            {/* Docs Header */}
            <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
                <div className="max-w-7xl mx-auto flex h-14 items-center px-6">
                    <div className="mr-4 hidden md:flex">
                        <button onClick={() => navigate('/dashboard')} className="mr-6 flex items-center space-x-2 font-bold text-slate-900 hover:text-blue-600 transition-colors">
                            <ArrowLeft size={16} />
                            <span>Meeting Monitor</span>
                        </button>
                        <nav className="flex items-center space-x-6 text-sm font-medium">
                            <a href="#" className="text-slate-900 transition-colors hover:text-slate-900/80">Documentation</a>
                            <a href="#" className="text-slate-500 transition-colors hover:text-slate-900">Components</a>
                            <a href="#" className="text-slate-500 transition-colors hover:text-slate-900">API</a>
                        </nav>
                    </div>
                    <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
                        <div className="w-full flex-1 md:w-auto md:flex-none">
                            <button className="inline-flex items-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950 disabled:pointer-events-none disabled:opacity-50 border border-slate-200 bg-slate-50 shadow-sm hover:bg-slate-100 hover:text-slate-900 h-9 px-4 py-2 relative w-full justify-start text-sm text-slate-500 sm:pr-12 md:w-40 lg:w-64">
                                <span className="inline-flex">Search...</span>
                                <kbd className="pointer-events-none absolute right-1.5 top-1.5 hidden h-5 select-none items-center gap-1 rounded border bg-slate-100 px-1.5 font-mono text-[10px] font-medium text-slate-500 opacity-100 sm:flex">
                                    <span className="text-xs">⌘</span>K
                                </kbd>
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] md:gap-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-10 px-6 pt-10">
                {/* Docs Sidebar */}
                <aside className="fixed top-14 z-30 -ml-2 hidden h-[calc(100vh-3.5rem)] w-full shrink-0 overflow-y-auto border-r border-slate-100 md:sticky md:block">
                    <div className="py-6 pr-6 lg:py-8">
                        <h4 className="mb-1 rounded-md px-2 py-1 text-sm font-semibold text-slate-900">Getting Started</h4>
                        <div className="grid grid-flow-row auto-rows-max text-sm">
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-900 font-medium bg-slate-100" href="#">Introduction</a>
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-500 hover:underline hover:text-slate-900" href="#">Installation</a>
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-500 hover:underline hover:text-slate-900" href="#">Theming</a>
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-500 hover:underline hover:text-slate-900" href="#">CLI</a>
                        </div>
                        <h4 className="mb-1 rounded-md px-2 py-1 text-sm font-semibold text-slate-900 mt-6">Architecture</h4>
                        <div className="grid grid-flow-row auto-rows-max text-sm">
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-500 hover:underline hover:text-slate-900" href="#">Components</a>
                            <a className="group flex w-full items-center rounded-md border border-transparent px-2 py-1.5 text-slate-500 hover:underline hover:text-slate-900" href="#">Utilities</a>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="relative py-6 lg:gap-10 lg:py-8 xl:grid xl:grid-cols-[1fr_300px]">
                    <div className="mx-auto w-full min-w-0">
                        <div className="mb-4 flex items-center space-x-1 text-sm text-slate-500">
                            <span className="truncate">Docs</span>
                            <ChevronRight size={14} />
                            <span className="font-medium text-slate-900">Introduction</span>
                        </div>

                        <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl text-slate-900 mb-6">
                            Introduction
                        </h1>

                        <p className="leading-7 text-slate-600 text-lg mb-8">
                            Meeting Monitor is a meeting intelligence platform designed to help you capture, analyze, and optimize your workflows using advanced machine learning models.
                        </p>

                        <div className="my-6 w-full overflow-y-auto rounded-lg bg-slate-950 p-4">
                            <code className="relative rounded bg-slate-950 px-[0.3rem] py-[0.2rem] font-mono text-sm text-slate-50 sm:text-base">
                                $ npm install @meeting-monitor/sdk
                            </code>
                        </div>

                        <div className="space-y-8 mt-10">
                            <div>
                                <h2 className="scroll-m-20 border-b border-slate-200 pb-2 text-3xl font-semibold tracking-tight first:mt-0 mb-4 text-slate-900 flex items-center">
                                    What is Meeting Monitor?
                                </h2>
                                <p className="leading-7 text-slate-600 mb-4">
                                    Meeting Monitor acts as a layer between your meeting software (Zoom, Teams, Google Meet) and your project management tools. It automatically:
                                </p>
                                <ul className="my-6 ml-6 list-disc [&>li]:mt-2 text-slate-600">
                                    <li>Transcribes audio in real-time.</li>
                                    <li>Identifies action items and assigns them to team members.</li>
                                    <li>Analyzes sentiment and engagement levels.</li>
                                </ul>
                            </div>

                            <div>
                                <h2 className="scroll-m-20 border-b border-slate-200 pb-2 text-3xl font-semibold tracking-tight first:mt-0 mb-4 text-slate-900">
                                    Authentication
                                </h2>
                                <p className="leading-7 text-slate-600 mb-4">
                                    All API requests must be authenticated using a Bearer token.
                                </p>
                                <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                                    <div className="flex gap-2 font-mono text-xs">
                                        <span className="text-blue-600">GET</span>
                                        <span className="text-slate-500">https://api.meeting-monitor.com/v1/meetings</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Table of Contents */}
                    <div className="hidden text-sm xl:block">
                        <div className="sticky top-16 -mt-10 max-h-[calc(var(--vh)-4rem)] overflow-y-auto pt-10">
                            <p className="mb-3 font-medium text-slate-900">On this page</p>
                            <ul className="space-y-2">
                                <li><a href="#" className="block text-slate-500 hover:text-slate-900">What is Meeting Monitor?</a></li>
                                <li><a href="#" className="block text-slate-500 hover:text-slate-900">Authentication</a></li>
                                <li><a href="#" className="block text-slate-500 hover:text-slate-900">FAQ</a></li>
                            </ul>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default DocsView;