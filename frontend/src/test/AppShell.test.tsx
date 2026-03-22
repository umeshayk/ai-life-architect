import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { AppProviders } from "../app/AppProviders";
import { AppShell } from "../layouts/AppShell";
import { DashboardPage } from "../pages/DashboardPage";

test("renders the foundation dashboard page inside the app shell", async () => {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppShell />,
        children: [{ index: true, element: <DashboardPage /> }],
      },
    ],
    { initialEntries: ["/"] },
  );

  render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  );

  expect(await screen.findByRole("heading", { name: /foundation/i })).toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: /primary navigation/i })).toBeInTheDocument();
});
