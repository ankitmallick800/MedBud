import { BrowserRouter, Route, Routes } from "react-router-dom";
import { DiseasePage } from "./components/DiseasePage";
import { HomePage } from "./components/HomePage";
import { Layout } from "./components/Layout";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path=":diseaseId" element={<DiseasePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
