import type { Component } from 'solid-js';

import logo from './logo.svg';
import styles from './App.module.css';
import Table from './table'

const App: Component = () => {
  return (
    <div class={styles.App}>
      <Table/>
    </div>
  );
};

export default App;
