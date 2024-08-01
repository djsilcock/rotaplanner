import type { Component } from 'solid-js';

import logo from './logo.svg';
import styles from './App.module.css';
import Table from './table'
import { QueryClient,QueryClientProvider } from '@tanstack/solid-query';
const client=new QueryClient()
const App: Component = () => {
  return (
    <QueryClientProvider client={client}>
    <div class={styles.App}>
      <Table/>
    </div>
    </QueryClientProvider>
  );
};

export default App;
