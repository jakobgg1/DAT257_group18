import { useState } from 'react'

import './App.css'
import InputField from './Components/temp'
import {useNavigate} from 'react-router-dom'

function App() {

  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    if(username  === "admin" && password === "megadogsab123"){
      alert("Login successful");
      window.location.href = "webpage/map.html"
    }else{
      alert("Invalid username or password");
    }
  }
    
  return (
    <div className="login-container">
    <h2 className="title">Login</h2>
      <form action="#" className="login-form" onSubmit={handleLogin}>

        <InputField type="text" placeholder="Username" icon="person" value={username} onChange={(e)=> setUsername(e.target.value)} />
        <InputField type="password" placeholder="Password" icon="key" value={password} onChange={(e) => setPassword(e.target.value)} />
  
      
      <button type="submit" className="login-button">Log in</button>
      </form>

      </div>
    
  )
  

 
  
}


export default App
