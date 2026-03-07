import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';
import { render } from '@testing-library/react';
import { router } from '@/router';

const queryClient = new QueryClient();

test('app shell renders', () => {
  const { container } = render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>);
  expect(container).toMatchSnapshot();
});
