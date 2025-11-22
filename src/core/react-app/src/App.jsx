import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MainLayout } from "@/components/layout";
import {
  DashboardPage,
  GeografiaPage,
  TemporalPage,
  VictimasPage,
  ClimaPage,
  ChatbotPage,
  PrediccionesPage,
} from "@/pages";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="geografia" element={<GeografiaPage />} />
          <Route path="temporal" element={<TemporalPage />} />
          <Route path="victimas" element={<VictimasPage />} />
          <Route path="clima" element={<ClimaPage />} />
          <Route path="chatbot" element={<ChatbotPage />} />
          <Route path="predicciones" element={<PrediccionesPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
