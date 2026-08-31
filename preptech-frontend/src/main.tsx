import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// Importamos el routeTree desde la ubicación correcta (al mismo nivel en src)
import { routeTree } from './routeTree.gen';
import './styles.css';

// Instanciamos el cliente de consultas que usa tu aplicación
const queryClient = new QueryClient();

// Creamos el router inyectando el contexto de queryClient que exige TypeScript
const router = createRouter({ 
  routeTree,
  context: { queryClient }
});

// Registramos el router para autocompletado de tipos
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById('root')!;
if (!rootElement.innerHTML) {
  const root = createRoot(rootElement);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>
  );
}